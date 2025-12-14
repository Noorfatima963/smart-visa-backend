from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

def send_verification_email(user, request=None):
    """
    Sends a verification email to the user.
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Ideally this URL should be your Frontend URL
    # For now we'll assume a localhost frontend or just print the tokens
    # We can also construct an absolute URI to the backend verify endpoint if checking via API directly
    
    # Example Backend Verification Link (if user clicks, it hits API directly - usually GET)
    # Or Frontend Link: http://localhost:3000/verify-email/{uid}/{token}
    
    # Let's assume a generic link for now.
    # checking if request is provided to build absolute uri
    if request:
        # This points to the backend VerifyEmailView if we implement it as GET
        # protocol = 'https' if request.is_secure() else 'http'
        # domain = request.get_host()
        # verification_url = f"{protocol}://{domain}/api/users/verify-email/{uid}/{token}/"
        pass

    # Using a placeholder frontend URL
    verification_url = f"http://localhost:3000/auth/verify-email?uid={uid}&token={token}"

    subject = 'Verify your email address'
    html_content = render_to_string('emails/verification_email.html', {
        'user': user,
        'verification_url': verification_url
    })
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.EMAIL_HOST_USER, # From email
        [user.email] # To email
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
