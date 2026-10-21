from django.utils.http import urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage


def SETupCOOKIE(response, key, value):
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=False,
        samesite='Strict',
        path='/',
    )

def send_verif_email(request, user):
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_link = f"http://{current_site.domain}/activate/{uid}/{token}"

    email_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verify Your Email</title>
    </head>
    <body>
        <p>Hi {user.first_name},</p>
        <p>Thank you for registering with Smart Parking. Please click the link below to verify your email address:</p>
        <p>
            <a href="{activation_link}">Verify Email</a>
        </p>
        <p>If you did not register for this account, please ignore this email.</p>
        <p>Thank you,<br>Smart Parking Team</p>
    </body>
    </html>
    """

    email = EmailMessage('Activate Your Account', email_body, to=[user.email])
    email.content_subtype = 'html'
    email.send()
