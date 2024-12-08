from django.core.mail import send_mail
from stationarymanagement.settings import EMAIL_HOST_USER
from django.conf import settings

def send_forget_password_mail(email, token):
    subject = 'Request For Password Reset Of SSMS'
    message = f'Click on this link to reset password for your Somaiya Stationary Management System account: http://127.0.0.1:8000/change_password/{token}/'
    email_from = EMAIL_HOST_USER
    recipient_list = [email]
    
    send_mail(subject, message, email_from, recipient_list)
    
    return True