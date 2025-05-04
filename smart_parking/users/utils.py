import pytz
from datetime import datetime, timedelta
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from rest_framework.response import Response
from rest_framework import status
import logging
logger = logging.getLogger(__name__)

def SETupCOOKIE(response, key, value, max_age):
    local_tz = pytz.timezone('Africa/Algiers')  
    local_time = datetime.now(local_tz)  
    expires_local = local_time + timedelta(seconds=max_age)
    expires_utc = expires_local.astimezone(pytz.utc)
    
    logger.info(f"Setting cookie '{key}' with value '{value}'")

    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=False,  
        samesite='Strict',  
        path='/',
        max_age=max_age,
        expires=expires_utc.strftime("%a, %d-%b-%Y %H:%M:%S GMT")  
    )
    
def send_verif_email(request , user) : 
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://{current_site.domain}/auth/activate/{uid}/{token}/"

      
            subject = 'Activate Your Account'
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

            # Send email
            email = EmailMessage(subject, email_body, to=[user.email])
            email.content_subtype = 'html' 
            email.send()
            return Response({'message': 'User registered successfully. Please check your email to verify your account.' , 'value' : 1}, status=status.HTTP_201_CREATED)

    
