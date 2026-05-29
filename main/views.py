from collections import Counter
from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

from django.conf import settings

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse


from django.db.models import *
from .forms import *
from .models import *
from .geo import apply_geo_to_dream, get_client_ip
from .dream_symbols import resolve_symbol_tags
# Checklist
# Add Sections
# Advertising Goodgle Adsense 
# Payment Mothod
# Adjust Submission Time
CLIENT_SECRET_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'secrets', 'client_secret.json')

def delete_duplicates(dream_post):
    duplicates = Dreams.objects.filter(
        title=dream_post.title
    ) | Dreams.objects.filter(
        dream=dream_post.dream
    )

    # If duplicates exist, delete them
    if duplicates.exists():
        duplicates.delete()

#@login_required
#@never_cache
def index(request):
    return render(request, "dreamapp/index.html", context={})


#def logout_view(request):
#    logout(request)
#    return redirect('main:login')


def consult(request):
    dreams = Dreams.objects.all()
    recent_submission = False

    Dreams.objects.filter(name="AlbertJipix").delete()
    Dreams.objects.filter(title="DON'T MISS OUT: CLAIM YOUR $50,000 WINNI").delete()
        
    if request.method == "POST":
        ip_address = get_client_ip(request)
        recent_submission = Dreams.objects.filter(ip_address=ip_address, submission_time__gte=timezone.now() - timedelta(days=1)).exists()
        
        if recent_submission:
            last_submission_time = Dreams.objects.filter(ip_address=ip_address).latest('submission_time').submission_time
            current_time = timezone.now()
            time_difference = current_time - last_submission_time
            wait_time_seconds = timedelta(days=1).total_seconds() - time_difference.total_seconds()

            hours, remainder = divmod(wait_time_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            wait_message = ""
            if hours >= 1:
                wait_message += f"{int(hours)} hour{'s' if int(hours) > 1 else ''}"
            if minutes >= 1:
                wait_message += f" {int(minutes)} minute{'s' if int(minutes) > 1 else ''}"
            if seconds >= 1:
                wait_message += f" {int(seconds)} second{'s' if int(seconds) > 1 else ''}"

            messages.error(request, f"To prevent spamming, please wait {wait_message} before resubmitting.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        dream_form = DreamForm(request.POST)
        if dream_form.is_valid() and not recent_submission:
            dream_post = dream_form.save(commit=False)
            dream_post.ip_address = ip_address
            apply_geo_to_dream(dream_post, ip_address)

            delete_duplicates(dream_post)   

            sender = dream_post.email 
            dream_post.save()
            pending_symbols = getattr(dream_form, '_pending_symbol_names', [])
            if pending_symbols:
                dream_post.symbols.set(resolve_symbol_tags(pending_symbols))
            Dreams.objects.filter(name="AlbertJipix").delete()

            from_email = 'dreamanalytica@outlook.com'
            to_email = 'dreamanalytica08@gmail.com'
            
            subject = "New Dream Submission"
            context = {
                "name": dream_post.name,
                "mbti_type": dream_post.mbti_type,
                "email": dream_post.email,
                "title": dream_post.title,
                "dream": dream_post.dream,
                "scale": dream_post.scale,
                "pub": dream_post.pub,
                "age": dream_post.age,
                "country_name": dream_post.country_name,
                "region": dream_post.region,
                "city": dream_post.city,
            }

            html_message = render_to_string("dreamapp/email_templates/dream_submission.html", context)
            plain_message = strip_tags(html_message)
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=from_email,
                to=[to_email, sender],
            )
            email.attach_alternative(html_message, "text/html")
            #email.send(fail_silently=True)
            
            return HttpResponseRedirect(reverse('main:dreams'))
        else:
            messages.error(request, "Invalid form data. Please check the entered information.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    else:
        dream_form = DreamForm()

    mbti_choices = DreamForm.MBTI_CHOICES
    gender_choices = DreamForm.GENDER_CHOICES
    symbol_suggestions = DreamSymbol.objects.all()[:200]

    return render(request, "dreamapp/consult.html", context={
        "dreams": dreams,
        "dream_form": dream_form,
        "recent_submission": recent_submission,
        "mbti_choices": mbti_choices,
        'gender_choices': gender_choices,
        'symbol_suggestions': symbol_suggestions,
    })



def dreams(request):
    reply_form = ReplyForm()
    dreams = Dreams.objects.all()

    avg_result = dreams.filter(active=True).aggregate(Avg('scale'))['scale__avg']
    average_scale = round(avg_result, 2) if avg_result is not None else None

    duplicates = Dreams.objects.values('title', 'dream').annotate(count=Count('id')).filter(count__gt=1)
    for duplicate in duplicates:
        Dreams.objects.filter(
            name=duplicate['name'],
        ).delete() 

    Dreams.objects.filter(name__in=["AlbertJipix", "Davidbiani","Search Engine Index"]).delete()

    if average_scale is not None:
        if average_scale > 3.5:
            health_status = "balanced"
            health_color = "#53FFFB"
        elif average_scale < 2.5:
            health_status = "unbalanced"
            health_color = "#FF007D"
        else:
            health_status = "neutral"
            health_color = "#FFE66D"
    else:
        health_status = "No data available"
        health_color = "#FFE66D"

    if request.method == 'POST':
        if not request.user.is_authenticated:
            # Store the current URL in the session and redirect to login
            request.session['next'] = request.path
            messages.error(request, 'You need to be logged in to reply.')
            return redirect('main:login')  # Adjust the URL name as necessary

        ip_address = request.META.get('REMOTE_ADDR')
        reply_form = ReplyForm(request.POST)

        # Check if the user has submitted a reply in the last 24 hours
        recent_submission = Share.objects.filter(ip_address=ip_address, submission_time__gte=timezone.now() - timedelta(days=1)).exists()

        if recent_submission:
            last_submission_time = Share.objects.filter(ip_address=ip_address).latest('submission_time').submission_time
            current_time = timezone.now()
            time_difference = current_time - last_submission_time
            wait_time = timedelta(days=1) - time_difference

            messages.error(request, f"You have already submitted the form. Please wait {wait_time} before resubmitting.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        elif reply_form.is_valid():
            dream_id = request.POST.get('dream_id')
            dream_email = request.POST.get('dream_email')
            try:
                if dream_id:
                    dream_instance = get_object_or_404(Dreams, id=dream_id)
                else:
                    dream_instance = get_object_or_404(Dreams, email=dream_email)
                reply = reply_form.save(commit=False)
                reply.dream = dream_instance
                reply.reply = request.POST.get('reply')
                reply.pub = timezone.now()
                reply.save()

                # Record the submission
                Share.objects.create(ip_address=ip_address, submission_time=timezone.now())

                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            except Dreams.DoesNotExist:
                messages.error(request, "Dream not found. Please check the email address.")
            except Exception as e:
                print(f"Error: {e}")
                messages.error(request, "An error occurred. Please try again later.")
            
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, "Invalid form data. Please check the entered information.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    active_dreams = Dreams.objects.filter(active=True).prefetch_related('reply_set').order_by('-pub')
    dreams_with_replies = [
        {'dream': dream, 'replies': dream.reply_set.all()}
        for dream in active_dreams
    ]

    dream_count = active_dreams.count()

    from .wall_analytics import build_wall_analytics

    analytics = build_wall_analytics(active_dreams, dream_count)

    return render(request, "dreamapp/dreams.html", {
        "dreams_with_replies": dreams_with_replies,
        "dreams": dreams,
        "reply_form": reply_form,
        "average_scale": average_scale,
        "health_status": health_status,
        "health_color": health_color,
        "dream_count": dream_count,
        **analytics,
    })


CONTACT_TOPIC_LABELS = {
    'general': 'General question',
    'dream': 'Dream / analysis',
    'collaboration': 'Collaboration / press',
    'technical': 'Technical / app',
    'other': 'Other',
}


def _contact_topic_prefix(topic_key):
    label = CONTACT_TOPIC_LABELS.get(topic_key, CONTACT_TOPIC_LABELS['general'])
    return f'[Topic: {label}]\n\n'


def contact(request):
    contact_sent = request.session.pop('contact_sent', False)

    if request.method == "POST":
        ip_address = request.META.get('REMOTE_ADDR')
        recent_submission = Contact.objects.filter(
            ip_address=ip_address,
            submission_time__gte=timezone.now() - timedelta(seconds=1),
        ).exists()

        if recent_submission:
            last_submission_time = Contact.objects.filter(
                ip_address=ip_address,
            ).latest('submission_time').submission_time
            time_difference = timezone.now() - last_submission_time
            wait_time_seconds = timedelta(days=1).total_seconds() - time_difference.total_seconds()

            hours, remainder = divmod(wait_time_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            wait_message = ""
            if hours >= 1:
                wait_message += f"{int(hours)} hour{'s' if int(hours) > 1 else ''}"
            if minutes >= 1:
                wait_message += f" {int(minutes)} minute{'s' if int(minutes) > 1 else ''}"
            if seconds >= 1:
                wait_message += f" {int(seconds)} second{'s' if int(seconds) > 1 else ''}"

            messages.error(
                request,
                f"To prevent spamming, please wait {wait_message.strip()} before resubmitting.",
            )
            return redirect('main:contact')

        contact_form = ContactForm(request.POST)
        if contact_form.is_valid() and not recent_submission:
            topic_key = request.POST.get('contact_topic', 'general').strip().lower()
            if topic_key not in CONTACT_TOPIC_LABELS:
                topic_key = 'general'

            contact_post = contact_form.save(commit=False)
            contact_post.ip_address = ip_address
            body = (contact_post.desc or '').strip()
            contact_post.desc = _contact_topic_prefix(topic_key) + body
            contact_post.save()

            request.session['contact_sent'] = True
            messages.success(
                request,
                "Message received. We will reply to your email within 24–48 hours.",
            )
            return redirect('main:contact')

        topic_key = request.POST.get('contact_topic', 'general').strip().lower()
        if topic_key not in CONTACT_TOPIC_LABELS:
            topic_key = 'general'
        messages.error(request, "Please fix the highlighted fields below.")
        return render(
            request,
            "dreamapp/contact.html",
            {
                "contact_form": contact_form,
                "contact_sent": False,
                "contact_topic": topic_key,
            },
        )

    contact_form = ContactForm()
    return render(
        request,
        "dreamapp/contact.html",
        {
            "contact_form": contact_form,
            "contact_sent": contact_sent,
            "contact_topic": "general",
        },
    )



def app(request):
    return render(request, "dreamapp/app.html")

def about(request):
    return render(request, "dreamapp/about.html")

def error(request):
    return render(request, "dreamapp/error.html")






    '''
def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.set_password(form.cleaned_data['password'])
            new_user.save()
            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('main:login')
    else:
        form = UserRegistrationForm()
    return render(request, 'dreamapp/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Invalid email or password')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password')
    return render(request, 'dreamapp/login.html')



    if dreams.exists():
        for dream_post in dreams:
            file_path = f"dreams/{dream_post.id}.json"
            # Get the download URL for the file from Firebase Storage
            download_url = storage.child(file_path).get_url(None)
            # Make an HTTP GET request to the download URL
            response = requests.get(download_url)
            # Check if the request was successful
            if response.status_code == 200:
                # Read the JSON data from the response
                json_data = response.json()
                # Append the JSON data to the list
                all_json_data.append(json_data)
            else:
                print(f"Error: Unable to fetch JSON data for dream ID {dream_post.id} from Firebase Storage. Status code: {response.status_code}")
    else:
        print("No dreams found.")
    '''

    '''
    pub_str = dream_post.pub.strftime('%Y-%m-%d %H:%M:%S') if dream_post.pub else None

    dream_data = {
        'id': str(dream_post.id),
        'ip_address': dream_post.ip_address,
        'submission_time': dream_post.submission_time.strftime('%Y-%m-%d %H:%M:%S'),
        'name': dream_post.name,
        'mbti_type': dream_post.mbti_type,
        'email': dream_post.email,
        'phone': str(dream_post.phone),
        'title': dream_post.title,
        'dream': dream_post.dream,
        'active': dream_post.active,
        'pub': pub_str,
    }
    
    json_data = json.dumps(dream_data)

    file_path = os.path.join(os.getcwd(), f"{dream_post.id}.json")

    with open(file_path, 'w') as file:
        file.write(json_data)
    # Store the JSON data in Firebase storage
    storage.child("dreams").child(f"{dream_post.id}.json").put(file_path)
    '''
    