import uuid
from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator
from .dream_symbols import normalize_symbol_name


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
    age = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(13), MaxValueValidator(120)],
        help_text='Optional; used for collective pattern analysis.',
    )
    country_code = models.CharField(max_length=2, blank=True, default='')
    country_name = models.CharField(max_length=80, blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    geo_timezone = models.CharField(max_length=64, blank=True, default='')
    #child = models.ForeignKey('self', related_name='reps', blank=True, null=True, on_delete=models.CASCADE)

    pub = models.DateTimeField("date published", default=timezone.now)
    title = models.CharField(max_length=44)
    dream = models.TextField(default="")
    symbols = models.ManyToManyField(
        'DreamSymbol',
        blank=True,
        related_name='dreams',
        help_text='Normalized dream imagery tags for collective pattern analysis.',
    )
    scale = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    viewobj = models.IntegerField(default=0)
    timer = models.DateTimeField(blank=True,null=True)
    active = models.BooleanField(default=False)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dreams_posted',
    )

    class Meta:
        verbose_name = "dreams"
        ordering = ['-pub']

    def __str__(self):
        return f"Submission from {self.ip_address} at {self.submission_time}"
    
    def __str__(self):
        return str(self.email)

    def symbol_names(self):
        return list(self.symbols.values_list('name', flat=True))


class DreamSymbol(models.Model):
    """Canonical symbol tag (e.g. Snake) — one row per unique meaning, case-insensitive."""

    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'dream symbol'
        verbose_name_plural = 'dream symbols'
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                name='main_dreamsymbol_name_ci_unique',
            ),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = normalize_symbol_name(self.name)
        super().save(*args, **kwargs)


class DreamComment(models.Model):
    dream = models.ForeignKey(Dreams, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dream_comments',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=50)
    body = models.TextField()
    pub = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['pub']
        verbose_name = 'dream comment'
        verbose_name_plural = 'dream comments'

    def __str__(self):
        return f'{self.name} on {self.dream_id}'


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    birth_year = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text='Used to compute age on each new dream submission; past dreams keep their saved age.',
    )
    birth_year_updates_count = models.PositiveSmallIntegerField(
        default=0,
        help_text='Number of times birth year was saved (max 3).',
    )
    mbti_type = models.CharField(
        max_length=4,
        choices=Dreams.MBTI_CHOICES,
        blank=True,
        default='',
    )
    mbti_updates_count = models.PositiveSmallIntegerField(
        default=0,
        help_text='Number of times personality type was saved (max 3).',
    )
    country_code = models.CharField(max_length=2, blank=True, default='')
    country_name = models.CharField(max_length=80, blank=True, default='')
    country_locked = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'user profile'
        verbose_name_plural = 'user profiles'

    def __str__(self):
        return f'Profile for {self.user_id}'


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    comment = models.ForeignKey(
        DreamComment,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    dream = models.ForeignKey(
        Dreams,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'notification'
        verbose_name_plural = 'notifications'

    def __str__(self):
        return f'Notification for {self.recipient_id}'


class RegistrationAttempt(models.Model):
    """Tracks registration POSTs for IP rate limiting (not pending account data)."""
    ip_address = models.CharField(max_length=45, db_index=True)
    email = models.EmailField(max_length=254, blank=True, default='')
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'registration attempt'
        verbose_name_plural = 'registration attempts'

    def __str__(self):
        return f'{self.ip_address} at {self.created_at:%Y-%m-%d %H:%M}'


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
        return str(self.email)