from django.db import models, transaction
from django.core.exceptions import ValidationError
from django import forms
from django.conf import settings
from django.contrib.auth.models import User, AbstractUser, BaseUserManager
# databases faculty stationary requests assignement
# makemigrations = create changes and store in a file
# migrate = apply the pending changes created by makemigrations

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        
        # Check if the user already exists
        existing_user = self.get_queryset().filter(email=email).first()
        if existing_user:
            return existing_user
        
        # If user doesn't exist, create a new one
        username = email.split('@')[0]
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    FACULTY = 'faculty'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (FACULTY, 'Faculty'),
        (ADMIN, 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    branch = models.CharField(max_length=100)
    email = models.EmailField(unique=True) 
    objects = CustomUserManager()

    def __str__(self):
        return self.username
    
class faculty(models.Model):
    id = models.AutoField(primary_key=True)
    facultys_name = models.CharField(max_length=100)
    faculty_email = models.CharField(max_length=100)
    def __str__(self):
        return self.facultys_name
    
from django.db.models import Sum, F

class stationary(models.Model):
    id = models.AutoField(primary_key=True)
    stationary_name = models.CharField(max_length=100)
    issued_quantity = models.PositiveIntegerField()
    issued_date = models.DateField()
    issued_from = models.CharField(max_length=200)
    cost_per_item = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    @property
    def overall_issued_quantity(self):
        return stationary.objects.filter(stationary_name=self.stationary_name).aggregate(models.Sum('issued_quantity'))['issued_quantity__sum'] or 0

    @property
    def overall_assigned_quantity(self):
        return assignment.objects.filter(stationary__stationary_name=self.stationary_name).aggregate(models.Sum('assigned_quantity'))['assigned_quantity__sum'] or 0

    @property
    def available_quantity(self):
        return self.overall_issued_quantity - self.overall_assigned_quantity

    @available_quantity.setter
    def available_quantity(self, value):
        # You can raise an error here since available_quantity should be read-only
        raise AttributeError("Cannot set attribute 'available_quantity' directly.")

    def __str__(self):
        return self.stationary_name

class assignment(models.Model):
    id = models.AutoField(primary_key=True)
    faculty_name = models.CharField(max_length=100)
    stationary = models.ForeignKey('stationary', on_delete=models.CASCADE)
    assigned_quantity = models.PositiveIntegerField()
    assignment_date = models.DateField()
    notes = models.CharField(max_length=30, default='DEPT')
    
    @property
    def assigned_quantity_sum(self):
        return assignment.objects.filter(stationary__stationary_name=self.stationary.stationary_name).aggregate(models.Sum('assigned_quantity'))['assigned_quantity__sum'] or 0

    def save(self, *args, **kwargs):
        with transaction.atomic():
            overall_available_quantity = self.stationary.overall_issued_quantity - self.assigned_quantity_sum
            if self.assigned_quantity <= overall_available_quantity:
                self.stationary.save()
                super(assignment, self).save(*args, **kwargs)
            else:
                raise ValidationError("Not enough available quantity for the assignment.")

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            self.stationary.save()  # Save the changes to the stationary instance
            super().delete(*args, **kwargs)  # Call the superclass delete method

    def __str__(self):
        return self.faculty_name
        
class facultyrequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Seen', 'Seen'),
        ('Issued', 'Issued'),
        ('Ordered', 'Ordered'),
    ]
    faculty_name = models.CharField(max_length=100)
    faculty_gmail = models.CharField(max_length=200)
    item_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=50, default='-')
    request_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    
    def __str__(self):
        return self.faculty_name

import datetime
import os

def filepath(request, filename):
    old_filename = filename
    timeNow = datetime.datetime.now().strftime('%Y%m%d%H:%M:%S')
    filename = "%s%s" % (timeNow, old_filename)
    return os.path.join('uploads/', filename)

class StationaryBill(models.Model):
    caption = models.TextField(max_length=200, null=True)
    image = models.ImageField(upload_to=filepath, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.caption

class item(models.Model):
    id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=100)

    def __str__(self):
        return self.item_name
    
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    forget_password_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.user.username