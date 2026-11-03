from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, send_mail
from django.utils.encoding import force_bytes
from django.utils.html import escape
from django.utils.http import urlsafe_base64_encode


def SETupCOOKIE(response, key, value):
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite='Strict',
        path='/',
    )


def send_verif_email(request, user):
    current_site = get_current_site(request)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    scheme = 'https' if request.is_secure() else 'http'
    activation_link = f"{scheme}://{current_site.domain}/activate/{uid}/{token}"

    email_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verify Your Email</title>
    </head>
    <body>
        <p>Hi {escape(user.first_name)},</p>
        <p>Thank you for registering with Smart Parking. Please click the link below to verify your email address:</p>
        <p>
            <a href="{escape(activation_link)}">Verify Email</a>
        </p>
        <p>If you did not register for this account, please ignore this email.</p>
        <p>Thank you,<br>Smart Parking Team</p>
    </body>
    </html>
    """

    email = EmailMessage('Activate Your Account', email_body, to=[user.email])
    email.content_subtype = 'html'
    email.send()


def send_username_taken_email(email):
    send_mail(
        'Smart Parking registration',
        'Someone tried to register a Smart Parking account with this email address, '
        'but the chosen username is already taken. Pick another username and register again. '
        'If this was not you, ignore this email.',
        None,
        [email],
    )
