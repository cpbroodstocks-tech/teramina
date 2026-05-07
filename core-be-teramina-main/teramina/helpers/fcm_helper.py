import logging

logger = logging.getLogger("teramina")


def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None) -> bool:
    """
    Send FCM push notification. Returns True on success, False on failure.
    Uses firebase_admin.messaging (already initialized via firebase_admin).
    """
    try:
        import firebase_admin.messaging as messaging
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={k: str(v) for k, v in (data or {}).items()},
            token=fcm_token,
        )
        messaging.send(message)
        return True
    except Exception as exc:
        logger.warning("FCM send failed: %s", exc)
        return False


def notify_user_alert(user_id: str, alert_type: str, severity: str, message: str, cycle_id: str = ""):
    """
    Look up user's FCM token and send notification.
    Only send for severity 'high' or 'critical' to avoid spam.
    """
    from teramina.user.models.user_model import User
    if severity not in ("high", "critical"):
        return
    user = User.objects(id=user_id).first()
    if not user or not user.fcm_token:
        return
    title = "🚨 Critical Alert" if severity == "critical" else "⚠️ Farm Alert"
    send_push_notification(user.fcm_token, title, message[:100],
                           {"alert_type": alert_type, "cycle_id": cycle_id})
