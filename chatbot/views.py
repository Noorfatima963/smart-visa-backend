import json
import urllib.request
import urllib.error

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .context_builder import build_context


class ChatMessageView(APIView):
    """
    POST /api/chatbot/message/

    Request body:
    {
        "message": "Can I get into a US university with my profile?",
        "history": [
            { "role": "user",      "content": "Hi" },
            { "role": "assistant", "content": "Hello! How can I help?" }
        ]
    }

    Response:
    {
        "reply":          "Based on your profile...",
        "missing_fields": [],
        "tokens_used":    142
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message = (request.data.get('message') or '').strip()
        history = request.data.get('history') or []

        if not message:
            return Response(
                {'error': 'message is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not settings.GROQ_API_KEY:
            return Response(
                {'error': 'Chatbot is not configured. GROQ_API_KEY missing.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Build context from student profile + assessment
        ctx = build_context(request.user)

        if not ctx['has_profile']:
            return Response({
                'reply': (
                    "I can't find your profile yet. Please complete the onboarding "
                    "steps first so I can give you personalized advice! 🎓"
                ),
                'missing_fields': ctx['missing_fields'],
                'tokens_used': 0,
            })

        # Build messages array for Groq
        messages = []

        if ctx['system_prompt']:
            messages.append({'role': 'system', 'content': ctx['system_prompt']})

        # Add conversation history (last 10 turns max to stay within token limits)
        for turn in history[-10:]:
            role    = turn.get('role', 'user')
            content = turn.get('content', '')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': content})

        # Add the new user message
        messages.append({'role': 'user', 'content': message})

        # Call Groq API
        try:
            payload = json.dumps({
                'model':       settings.GROQ_MODEL,
                'messages':    messages,
                'max_tokens':  512,
                'temperature': 0.7,
            }).encode('utf-8')

            req = urllib.request.Request(
                settings.GROQ_API_URL,
                data=payload,
                headers={
                    'Content-Type':  'application/json',
                    'Authorization': f'Bearer {settings.GROQ_API_KEY}',
                    'User-Agent':    'SmartVisa/1.0',
                },
                method='POST',
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode('utf-8'))

            reply       = data['choices'][0]['message']['content'].strip()
            tokens_used = data.get('usage', {}).get('total_tokens', 0)

            return Response({
                'reply':          reply,
                'missing_fields': ctx['missing_fields'],
                'tokens_used':    tokens_used,
            })

        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8')
            return Response(
                {'error': f'Groq API error: {body}'},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            return Response(
                {'error': f'Chatbot unavailable: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class ChatSuggestionsView(APIView):
    """
    GET /api/chatbot/suggestions/

    Returns 4-5 smart suggested questions based on the student's profile state.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile   = request.user.profile
            education = profile.education_history.first()
            language  = profile.test_scores.first()
            financial = getattr(profile, 'financial_profile', None)
            country   = profile.target_country or 'USA'
            degree    = profile.target_degree_type or 'Masters'

            suggestions = []

            if education and language:
                suggestions.append(f"Am I eligible for {degree} in {country} with my current profile?")
            else:
                suggestions.append(f"What GPA and IELTS score do I need for {degree} in {country}?")

            if financial and financial.approx_savings:
                savings = float(financial.approx_savings)
                suggestions.append(f"Is ${savings:,.0f} enough to study in {country} for one year?")
            else:
                suggestions.append(f"How much money do I need to study in {country}?")

            suggestions.append(f"What documents do I need for a student visa to {country}?")
            suggestions.append("Which country is best for Computer Science Masters?")
            suggestions.append("How can I improve my admission chances?")

            return Response({'suggestions': suggestions[:5]})

        except Exception:
            return Response({
                'suggestions': [
                    "What GPA do I need for a US Masters?",
                    "How much does studying in the UK cost?",
                    "Which countries are easiest for Pakistani students?",
                    "What documents do I need for a student visa?",
                    "How can I improve my admission chances?",
                ]
            })
