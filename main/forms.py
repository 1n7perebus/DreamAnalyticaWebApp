from django import forms
from .models import *
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from phonenumber_field.formfields import PhoneNumberField

class UserRegistrationForm(forms.ModelForm):
    username = forms.CharField(
        max_length=30,
        validators=[RegexValidator(regex='^[a-zA-Z]*$', message='Username must contain only letters.')],
        label='Username'
    )
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return cd['password2']

class DreamForm(forms.ModelForm):
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

    email = forms.EmailField(required=True, label="Email")
    name = forms.CharField(required=True, label="Name")
    #phone = PhoneNumberField(required=False, label="Phone Number")
    title = forms.CharField(required=True, label="Title")
    dream = forms.CharField(required=True)
    active = forms.BooleanField(required=False)
    mbti_type = forms.ChoiceField(choices=MBTI_CHOICES, label="MBTI Type")
    gender = forms.ChoiceField(choices=GENDER_CHOICES, label="Gender", required=True)
    scale = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],  # Updated to 1-5 to match the model
        label="Dream Scale", 
        initial=3,  # Default scale to the middle value (3)
        widget=forms.RadioSelect,
        required=False
    )

    class Meta:
        model = Dreams
        fields = ['email', 'name', 'title', 'dream', 'active', 'mbti_type', 'gender', 'scale']



class ReplyForm(forms.ModelForm):
    reply = forms.CharField(required= True, label="Reply")
    class Meta:
        model = Reply
        fields = ['reply']


class ContactForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")
    name = forms.CharField(required=True, label="Name")
    phone = PhoneNumberField(required=False, label="Phone Number")

    class Meta:
        model = Contact
        fields = ['email', 'name', 'phone']