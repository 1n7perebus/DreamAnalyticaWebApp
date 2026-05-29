import re

import phonenumbers
from django import forms
from .models import *
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber

from .dream_symbols import parse_symbol_tags, resolve_symbol_tags


def normalize_contact_phone(raw):
    """
    Accept flexible user input (+1 293-939-9337, +1292929999, etc.)
    and return an E.164 PhoneNumber for storage, or None when empty.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None

    digits_only = re.sub(r'\D', '', text)
    has_plus = text.lstrip().startswith('+')

    if has_plus:
        candidate = '+' + digits_only
    elif len(digits_only) == 10:
        candidate = '+1' + digits_only
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        candidate = '+' + digits_only
    else:
        candidate = '+' + digits_only

    try:
        parsed = phonenumbers.parse(candidate, None)
    except phonenumbers.NumberParseException as exc:
        raise forms.ValidationError(
            'Enter a valid phone with country code (e.g. +1 293-939-9337).'
        ) from exc

    if not phonenumbers.is_valid_number(parsed):
        raise forms.ValidationError(
            'That phone number does not look valid. Include your country code.'
        )

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    return PhoneNumber.from_string(e164)

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
    dream_symbols = forms.CharField(
        required=True,
        label='Dream symbols',
        help_text='Add 1–5 key images (Enter or comma). Case-insensitive; check spelling.',
        widget=forms.HiddenInput(),
    )
    active = forms.BooleanField(required=False)
    mbti_type = forms.ChoiceField(choices=MBTI_CHOICES, label="MBTI Type")
    gender = forms.ChoiceField(choices=GENDER_CHOICES, label="Gender", required=True)
    age = forms.IntegerField(
        required=False,
        min_value=13,
        max_value=120,
        label="Age (optional)",
        widget=forms.NumberInput(attrs={'min': 13, 'max': 120, 'inputmode': 'numeric'}),
    )
    scale = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(1, 6)],  # Updated to 1-5 to match the model
        label="Dream Scale", 
        initial=3,  # Default scale to the middle value (3)
        widget=forms.RadioSelect,
        required=False
    )

    class Meta:
        model = Dreams
        fields = [
            'email', 'name', 'title', 'dream', 'active',
            'mbti_type', 'gender', 'age', 'scale',
        ]

    def clean_dream_symbols(self):
        raw = self.cleaned_data.get('dream_symbols', '')
        try:
            names = parse_symbol_tags(raw)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc
        if not names:
            raise forms.ValidationError(
                'Add at least one dream symbol (comma-separated), e.g. snake, water, flying.'
            )
        self._parsed_symbol_names = names
        return ', '.join(names)

    def save(self, commit=True):
        dream = super().save(commit=False)
        symbol_names = getattr(self, '_parsed_symbol_names', [])
        if commit:
            dream.save()
            if symbol_names:
                dream.symbols.set(resolve_symbol_tags(symbol_names))
        else:
            self._pending_symbol_names = symbol_names
        return dream


class ReplyForm(forms.ModelForm):
    reply = forms.CharField(required= True, label="Reply")
    class Meta:
        model = Reply
        fields = ['reply']


class ContactForm(forms.ModelForm):
    email = forms.EmailField(required=True, label="Email")
    name = forms.CharField(required=True, label="Name")
    phone = forms.CharField(
        required=False,
        label="Phone (optional)",
        max_length=32,
    )
    desc = forms.CharField(required=True, label="Message")

    class Meta:
        model = Contact
        fields = ['email', 'name', 'phone', 'desc']

    def clean_phone(self):
        return normalize_contact_phone(self.cleaned_data.get('phone'))

    def save(self, commit=True):
        instance = super().save(commit=False)
        phone = self.cleaned_data.get('phone')
        if phone:
            instance.phone = phone
        if commit:
            instance.save()
        return instance