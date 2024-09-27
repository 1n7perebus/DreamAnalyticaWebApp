import os
import datetime
import uuid
from django.db import models
from django.utils import timezone
from datetime import datetime
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator


class Dreams(models.Model):
    search_fields = ['email', 'title', 'pub', 'dream','id']

    MBTI_CHOICES = [
        ('', ''),
        ('INTJ', 'INTJ'),
        ('INTP', 'INTP'),
        ('ENTJ', 'ENTJ'),
        ('ENTP', 'ENTP'),
        ('INFJ', 'INFJ'),
        ('INFP', 'INFP'),
        ('ENFJ', 'ENFJ'),
        ('ENFP', 'ENFP'),
        ('ISTJ', 'ISTJ'),
        ('ISFJ', 'ISFJ'),
        ('ESTJ', 'ESTJ'),
        ('ESFJ', 'ESFJ'),
        ('ISTP', 'ISTP'),
        ('ISFP', 'ISFP'),
        ('ESTP', 'ESTP'),
        ('ESFP', 'ESFP'),
    ]

    GENDER_CHOICES = [
        ('', ''),
        ('Female', 'Female'),
        ('Male', 'Male'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ip_address = models.CharField(max_length=45, default="")
    submission_time = models.DateTimeField(default=timezone.now)

    name = models.CharField(max_length=50, default="")
    email = models.EmailField(max_length=200, default="")
    #phone = PhoneNumberField(default="+10000000000")

    mbti_type = models.CharField(max_length=4, choices=MBTI_CHOICES, default='')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='')
    #child = models.ForeignKey('self', related_name='reps', blank=True, null=True, on_delete=models.CASCADE)

    pub = models.DateTimeField("date published", default=timezone.now)
    title = models.CharField(max_length=44)
    dream = models.TextField(default="")
    scale = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    viewobj = models.IntegerField(default=0)
    timer = models.DateTimeField(blank=True,null=True)
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "dreams"
        ordering = ['-pub']

    def __str__(self):
        return f"Submission from {self.ip_address} at {self.submission_time}"
    
    def __str__(self):
        return str(self.email)
    
class Reply(models.Model):
    dream = models.ForeignKey(Dreams, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, default="R")  # Field made optional
    reply = models.TextField()
    pub = models.DateTimeField(default=datetime.now)

    def __str__(self):
        return str(self.dream.id)
    
    
class Contact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    ip_address = models.CharField(max_length=45, default="")
    submission_time = models.DateTimeField(default=timezone.now)

    name = models.CharField(max_length=50, default="")
    email = models.EmailField(max_length=200, default="")
    phone = PhoneNumberField(default="+10000000000")
    desc = models.TextField(default="")
    pub = models.DateTimeField("date published", default=timezone.now)

    class Meta:
        verbose_name = "contact"
        ordering = ['-pub']

    def __str__(self):
        return f"Submission from {self.ip_address} at {self.submission_time}"
    
    def __str__(self):
        return str(self.email)