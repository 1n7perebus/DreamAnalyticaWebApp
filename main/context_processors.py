from .models import Notification
from .profile_helpers import unread_notification_count


def nav_notifications(request):
    if request.user.is_authenticated:
        recent = (
            Notification.objects.filter(recipient=request.user)
            .select_related('comment', 'dream')
            .order_by('-created_at')[:8]
        )
        return {
            'unread_notification_count': unread_notification_count(request.user),
            'recent_notifications': recent,
        }
    return {'unread_notification_count': 0, 'recent_notifications': []}
