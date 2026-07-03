import requests
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class ResendAPIBackend(BaseEmailBackend):
    """Send Django email messages through Resend's HTTPS API."""

    api_url = 'https://api.resend.com/emails'
    timeout = 10

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        sent_count = 0
        for message in email_messages:
            if self._send(message):
                sent_count += 1
        return sent_count

    def _send(self, message):
        if not message.to:
            return False

        payload = {
            'from': message.from_email,
            'to': message.to,
            'subject': message.subject,
            'text': message.body,
        }
        if message.cc:
            payload['cc'] = message.cc
        if message.bcc:
            payload['bcc'] = message.bcc
        if message.reply_to:
            payload['reply_to'] = message.reply_to

        html_body = self._get_html_body(message)
        if html_body:
            payload['html'] = html_body

        headers = {
            'Authorization': f'Bearer {settings.RESEND_API_KEY}',
            'Content-Type': 'application/json',
            'User-Agent': 'IslamicJobsDjango/1.0',
        }

        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except Exception:
            if self.fail_silently:
                return False
            raise

        return True

    @staticmethod
    def _get_html_body(message):
        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                return content
        return None
