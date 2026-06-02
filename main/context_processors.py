from .models import Notification
from .profile_helpers import unread_notification_count


def nav_notifications(request):
    if request.user.is_authenticated:
        header_limit = 10
        recent = (
            Notification.objects.filter(recipient=request.user)
            .select_related('comment', 'dream')
            .order_by('-created_at')[:header_limit]
        )
        unread_count = unread_notification_count(request.user)
        return {
            'unread_notification_count': unread_count,
            'unread_notification_count_display': '99+' if unread_count > 99 else str(unread_count),
            'recent_notifications': recent,
            'recent_notifications_limit': header_limit,
            'recent_notifications_has_more': Notification.objects.filter(recipient=request.user).count() > header_limit,
        }
    return {
        'unread_notification_count': 0,
        'unread_notification_count_display': '0',
        'recent_notifications': [],
        'recent_notifications_limit': 10,
        'recent_notifications_has_more': False,
    }
