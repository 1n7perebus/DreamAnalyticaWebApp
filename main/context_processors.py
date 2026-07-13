from django.urls import reverse

from .models import Notification
from .profile_helpers import (
    get_or_create_profile,
    is_profile_complete,
    profile_setup_reminder_message,
    unread_notification_count,
)


def nav_notifications(request):
    if request.user.is_authenticated:
        header_limit = 10
        recent = list(
            Notification.objects.filter(recipient=request.user)
            .select_related('comment', 'dream')
            .order_by('-created_at')[:header_limit]
        )
        unread_count = unread_notification_count(request.user)

        profile = get_or_create_profile(request.user)
        needs_setup = not is_profile_complete(request.user, profile)
        url_name = getattr(getattr(request, 'resolver_match', None), 'url_name', None)
        show_banner = needs_setup and url_name != 'complete_profile'

        if needs_setup:
            unread_count += 1

        return {
            'unread_notification_count': unread_count,
            'unread_notification_count_display': '99+' if unread_count > 99 else str(unread_count),
            'recent_notifications': recent,
            'recent_notifications_limit': header_limit,
            'recent_notifications_has_more': (
                Notification.objects.filter(recipient=request.user).count() > header_limit
            ),
            'profile_setup_needed': needs_setup,
            'show_profile_setup_banner': show_banner,
            'profile_setup_url': reverse('main:complete_profile'),
            'profile_setup_reminder_message': profile_setup_reminder_message(),
        }
    return {
        'unread_notification_count': 0,
        'unread_notification_count_display': '0',
        'recent_notifications': [],
        'recent_notifications_limit': 10,
        'recent_notifications_has_more': False,
        'profile_setup_needed': False,
        'show_profile_setup_banner': False,
        'profile_setup_url': '',
        'profile_setup_reminder_message': '',
    }
