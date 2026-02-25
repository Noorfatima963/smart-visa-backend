import json
import logging
import google.generativeai as genai
from django.conf import settings
from .models import UserDocument
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Try to configure Gemini API if key is available
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
except AttributeError:
    logger.warning("GEMINI_API_KEY not found in settings! Document AI checker will fail.")

# Global ThreadPool for background AI processing
ai_thread_pool = ThreadPoolExecutor(max_workers=3)

def submit_ai_verification(user_document: UserDocument):
    """
    Submits the document verification task to the background ThreadPool
    so it doesn't block the main upload API response.
    """
    user_document.ai_status = UserDocument.AIStatusChoice.PROCESSING
    user_document.save(update_fields=['ai_status'])
    ai_thread_pool.submit(verify_document_with_ai, user_document)

def verify_document_with_ai(user_document: UserDocument):
    """
    Synchronously verifies a document using Gemini's Multimodal LLM.
    We pass the file location to Gemini, ask it to extract details,
    and verify if it matches the expected DocumentDefinition.
    """
    try:

        # 2. Get the file path
        if not user_document.file or not user_document.file.path:
            raise ValueError("No file attached to this UserDocument.")
        
        file_path = user_document.file.path
        doc_definition = user_document.document_definition.name

        # 3. Setup Gemini Model
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 4. Upload file to Gemini API temporarily
        uploaded_file = genai.upload_file(file_path)

        # 5. Define the strict verification prompt
        prompt = f"""
        You are an elite, highly strict visa document Verification AI. 
        Your job is to look at the provided document and determine if it is a valid '{doc_definition}'.
        
        If it matches '{doc_definition}', extract all the useful data you can find (e.g., Name, Date, Balances, Scores, Institutes).
        If it does NOT match '{doc_definition}', explicitly state why it failed (e.g., "User uploaded a grocery receipt instead of a passport").

        You MUST respond in strict JSON format EXACTLY matching this schema with no markdown formatting around it:
        {{
            "is_match": true/false,
            "extracted_data": {{"key": "value"}},
            "rejection_reason": "string detailing why it failed, or null if is_match is true",
            "confidence_score": integer between 0-100
        }}
        """

        # 6. Call the LLM
        response = model.generate_content(
            [prompt, uploaded_file],
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1 # Low temperature for strict factual responses
            )
        )

        # 7. Parse the LLM response
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            raise ValueError(f"Gemini did not return valid JSON: {response.text}")

        # 8. Update Document Status
        is_match = result.get('is_match', False)
        
        user_document.ai_extracted_data = result.get('extracted_data', {})
        user_document.ai_confidence_score = result.get('confidence_score', 0)

        if is_match and user_document.ai_confidence_score >= 80:
            user_document.ai_status = UserDocument.AIStatusChoice.PASSED
            user_document.ai_rejection_reason = None
        else:
            user_document.ai_status = UserDocument.AIStatusChoice.FAILED
            user_document.ai_rejection_reason = result.get('rejection_reason', "AI determined document did not match requirements.")

        user_document.save(update_fields=['ai_status', 'ai_extracted_data', 'ai_rejection_reason', 'ai_confidence_score', 'status'])
        
        # 9. Cleanup uploaded file from Gemini servers
        genai.delete_file(uploaded_file.name)
        
        # 10. Send Email Notification
        _send_status_email(user_document)

    except Exception as e:
        logger.error(f"AI Verification Failed for Document {user_document.id}: {str(e)}")
        user_document.ai_status = UserDocument.AIStatusChoice.FAILED
        user_document.ai_rejection_reason = f"Internal AI System Error: {str(e)}"
        user_document.save(update_fields=['ai_status', 'ai_rejection_reason'])
        _send_status_email(user_document)

def _send_status_email(user_document: UserDocument):
    """
    Helper function to send the PASSED or FAILED HTML email 
    to the user after AI verification concludes.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.utils.html import strip_tags
    
    user = user_document.user
    if not user.email:
        return
        
    dashboard_url = settings.FRONTEND_URL + "/dashboard/documents" if hasattr(settings, 'FRONTEND_URL') else "http://localhost:3000/dashboard/documents"
    
    context = {
        'user': user,
        'document_name': user_document.document_definition.name,
        'dashboard_url': dashboard_url,
    }
    
    if user_document.ai_status == UserDocument.AIStatusChoice.PASSED:
        subject = f"✅ Document Verified: {user_document.document_definition.name}"
        context['extracted_data'] = user_document.ai_extracted_data
        html_message = render_to_string('documents/emails/document_passed.html', context)
    else:
        subject = f"⚠️ Action Required: {user_document.document_definition.name} Verification Failed"
        context['rejection_reason'] = user_document.ai_rejection_reason
        html_message = render_to_string('documents/emails/document_failed.html', context)
        
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER or 'noreply@smartvisa.com',
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=True
        )
    except Exception as e:
        logger.error(f"Failed to send AI status email to {user.email}: {str(e)}")
