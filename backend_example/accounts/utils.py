import os
import random
import hashlib
from django.core.mail import EmailMessage
from django.conf import settings
from .models import User, OneTimePassword
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework.exceptions import APIException, NotFound



def send_generated_otp_to_email(email, request): 
    subject = "Code de vérification pour votre inscription"
    otp=str(random.randint(10000, 99999))
    salt = os.urandom(32)
    
    hashed_otp = hashlib.pbkdf2_hmac(
        'sha256',
        otp.encode('utf-8'),
        salt,
        10000
    )
    
    final_hash = salt.hex() + hashlib.sha256(hashed_otp).hexdigest()
       
    user = User.objects.get(email=email)
    email_body = f"Bonjour {user.first_name}, votre code de vérification est {otp}"
    from_email = settings.EMAIL_HOST
       
    # Créer l'objet OTP avec le hash
    otp_obj = OneTimePassword.objects.create(user=user, otp_hash=final_hash)
       
    # Envoyer l'email
    d_email = EmailMessage(subject=subject, body=email_body, from_email=from_email, to=[user.email])
    d_email.send()


def send_normal_email(data):
    email=EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
        from_email=settings.EMAIL_HOST_USER,
        to=[data['to_email']]
    )
    email.send()
