'''app/tools/notification_tools.py - Notification tools'''
def send_notification(message: str, user_id: int = 1, channel: str = 'email') -> bool:
    '''Send notification via email/SMS/push'''
    channels = {'email': '📧', 'sms': '📱', 'push': '🔔'}
    icon = channels.get(channel, '📤')
    print(f"[{icon}] Notification to user {user_id}: {message}")
    return True

def send_bulk_notifications(messages: list, user_ids: list) -> int:
    '''Send bulk notifications'''
    sent = 0
    for msg, uid in zip(messages, user_ids):
        if send_notification(msg, uid):
            sent += 1
    return sent

