import re

import phonenumbers
from django import forms
from django.utils import timezone
from .models import *
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.phonenumber import PhoneNumber

from .country_data import COUNTRY_CHOICES
from .dream_symbols import parse_symbol_tags, resolve_symbol_tags
from .models import UserProfile


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

def unique_username_from_name(name, email):
    """Derive a unique username from display name, falling back to email local-part."""
    base = re.sub(r'[^a-zA-Z]', '', (name or '').strip())[:20]
    if not base:
        base = re.sub(r'[^a-zA-Z]', '', (email or '').split('@')[0])[:20] or 'user'
    username = base
    n = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{n}'
        n += 1
    return username


class UserRegistrationForm(forms.ModelForm):
    display_name = forms.CharField(max_length=50, label='Name')
    website = forms.CharField(
        required=False,
        label='Website',
        widget=forms.TextInput(attrs={
            'class': 'register-honeypot',
            'tabindex': '-1',
            'autocomplete': 'off',
            'aria-hidden': 'true',
        }),
    )
    country_code = forms.ChoiceField(
        choices=[('', 'Select country…')] + list(COUNTRY_CHOICES),
        label='Country',
        required=True,
    )
    birth_year = forms.TypedChoiceField(
        choices=[],
        coerce=int,
        required=True,
        label='Birth year',
        widget=forms.Select(attrs={'class': 'profile-native-select no-autoinit'}),
    )
    mbti_type = forms.ChoiceField(
        choices=[('', 'Select type…')] + [
            (value, label)
            for value, label in Dreams.MBTI_CHOICES
            if value
        ],
        label='Personality type',
        required=True,
    )
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .profile_helpers import birth_year_choices

        input_class = 'contact-field__input'
        for name in ['display_name', 'email', 'password', 'password2']:
            self.fields[name].widget.attrs['class'] = input_class
        self.fields['country_code'].widget.attrs['class'] = 'profile-native-select no-autoinit'
        self.fields['mbti_type'].widget.attrs['class'] = 'profile-native-select no-autoinit'
        self.fields['birth_year'].choices = [('', 'Select birth year…')] + birth_year_choices()

    def clean_display_name(self):
        from .spam_checks import looks_like_bot_display_name

        name = (self.cleaned_data.get('display_name') or '').strip()[:50]
        if not name:
            raise forms.ValidationError('Please enter your name.')
        if looks_like_bot_display_name(name):
            raise forms.ValidationError('Please enter a real display name.')
        return name

    def clean_website(self):
        if (self.cleaned_data.get('website') or '').strip():
            raise forms.ValidationError('Registration could not be completed.')
        return ''

    def clean_email(self):
        from .spam_checks import is_disposable_email

        email = (self.cleaned_data.get('email') or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        if is_disposable_email(email):
            raise forms.ValidationError('Please use a permanent email address, not a disposable inbox.')
        return email

    def clean_birth_year(self):
        from .profile_helpers import max_birth_year, min_birth_year

        birth_year = self.cleaned_data.get('birth_year')
        if birth_year in (None, ''):
            raise forms.ValidationError('Please select your birth year.')
        if birth_year < min_birth_year() or birth_year > max_birth_year():
            raise forms.ValidationError('Please choose a valid birth year.')
        return birth_year

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return cd['password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        display_name = self.cleaned_data['display_name'].strip()[:50]
        user.first_name = display_name
        user.username = unique_username_from_name(display_name, user.email)
        if commit:
            user.save()
        return user

    def save_profile(self, user):
        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                'birth_year': self.cleaned_data['birth_year'],
                'birth_year_updates_count': 1,
                'mbti_type': self.cleaned_data['mbti_type'],
                'mbti_updates_count': 1,
                'country_code': self.cleaned_data['country_code'],
                'country_name': dict(COUNTRY_CHOICES).get(self.cleaned_data['country_code'], ''),
                'country_locked': True,
            },
        )

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


class ProfileCountryForm(forms.Form):
    country_code = forms.ChoiceField(
        choices=[('', 'Select country…')] + list(COUNTRY_CHOICES),
        label='Country',
        required=True,
    )


class ProfileMbtiForm(forms.ModelForm):
    mbti_type = forms.ChoiceField(
        choices=[],
        required=True,
        label='Personality type',
        widget=forms.Select(attrs={'class': 'profile-native-select no-autoinit'}),
    )

    class Meta:
        model = UserProfile
        fields = ['mbti_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [('', 'Select type…')] + [
            (value, label)
            for value, label in Dreams.MBTI_CHOICES
            if value
        ]
        self.fields['mbti_type'].choices = choices

    def clean_mbti_type(self):
        value = (self.cleaned_data.get('mbti_type') or '').strip().upper()
        valid = {code for code, _ in Dreams.MBTI_CHOICES if code}
        if value not in valid:
            raise forms.ValidationError('Please choose a valid personality type.')
        return value


class ProfileBirthYearForm(forms.ModelForm):
    birth_year = forms.TypedChoiceField(
        choices=[],
        coerce=int,
        required=True,
        label='Birth year',
        widget=forms.Select(attrs={'class': 'profile-native-select no-autoinit'}),
    )

    class Meta:
        model = UserProfile
        fields = ['birth_year']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .profile_helpers import birth_year_choices

        choices = [('', 'Select birth year…')] + birth_year_choices()
        self.fields['birth_year'].choices = choices

    def clean_birth_year(self):
        from .profile_helpers import max_birth_year, min_birth_year

        birth_year = self.cleaned_data.get('birth_year')
        if birth_year in (None, ''):
            return None
        if birth_year < min_birth_year() or birth_year > max_birth_year():
            raise forms.ValidationError('Please choose a valid birth year.')
        return birth_year


class CommentForm(forms.ModelForm):
    body = forms.CharField(
        required=True,
        label='Comment',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Share your thoughts…',
        }),
    )

    class Meta:
        model = DreamComment
        fields = ['body']


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


class AdminContactReplyForm(forms.Form):
    to_email = forms.EmailField(
        required=True,
        label='Send to',
        widget=forms.EmailInput(attrs={'class': 'contact-field__input'}),
    )
    message = forms.CharField(
        required=True,
        label='Message',
        widget=forms.Textarea(
            attrs={
                'class': 'contact-field__input',
                'rows': 8,
                'placeholder': 'Write your response message...',
            }
        ),
    )