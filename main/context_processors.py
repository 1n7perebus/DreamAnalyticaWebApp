from .profile_helpers import unread_notification_count


def nav_notifications(request):
    if request.user.is_authenticated:
        return {'unread_notification_count': unread_notification_count(request.user)}
    return {'unread_notification_count': 0}
