# core/jarvis/notification_center.py -- MESAN Omega Notification Center v1.0
"""
Centro de notificaciones multicanal.
Preparado para Email, WhatsApp, Slack, Teams, Telegram, Webhook.
"""
import os
import logging
import json
from collections import deque
from datetime import datetime, timezone
logger = logging.getLogger("mesan.guardian.notifications")

NOTIFY_EVENTS = ["CRITICAL_ALERT","WAR_ROOM","ROLLBACK","SERVICE_DOWN","PAYMENT_FAILED","AI_OFFLINE"]

class NotificationCenter:
    def __init__(self):
        self.version = "1.0.0"
        self._queue = deque(maxlen=500)
        self._sent = deque(maxlen=500)
        self._channels = {
            "email": {"enabled": bool(os.getenv("SMTP_HOST")), "handler": "_send_email"},
            "whatsapp": {"enabled": bool(os.getenv("WHATSAPP_API_KEY")), "handler": "_send_whatsapp"},
            "slack": {"enabled": bool(os.getenv("SLACK_WEBHOOK_URL")), "handler": "_send_slack"},
            "teams": {"enabled": bool(os.getenv("TEAMS_WEBHOOK_URL")), "handler": "_send_teams"},
            "telegram": {"enabled": bool(os.getenv("TELEGRAM_BOT_TOKEN")), "handler": "_send_telegram"},
            "webhook": {"enabled": bool(os.getenv("NOTIFICATION_WEBHOOK_URL")), "handler": "_send_webhook"},
        }
        active = [k for k, v in self._channels.items() if v["enabled"]]
        logger.info("[Notifications] v%s | canales activos: %s", self.version, active or ["ninguno"])

    def notify(self, event, severity, message, payload=None):
        notification = {
            "id": "NOTIF-{}".format(int(datetime.now(timezone.utc).timestamp() * 1000)),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "severity": severity,
            "message": message,
            "payload": payload or {},
            "channels_sent": [],
            "status": "PENDING",
        }
        self._queue.append(notification)
        if event in NOTIFY_EVENTS or severity in ("CRITICAL", "HIGH"):
            results = self._dispatch(notification)
            notification["channels_sent"] = results
            notification["status"] = "SENT" if results else "NO_CHANNELS"
        self._sent.append(notification)
        return notification

    def _dispatch(self, notification):
        results = []
        for name, config in self._channels.items():
            if not config["enabled"]:
                continue
            try:
                handler = getattr(self, config["handler"], None)
                if handler:
                    r = handler(notification)
                    results.append({"channel": name, "status": r.get("status", "OK")})
            except Exception as e:
                results.append({"channel": name, "status": "FAILED", "error": str(e)})
                logger.error("[Notifications] %s failed: %s", name, e)
        return results

    def _send_email(self, notif):
        logger.info("[Notifications] Email queued: %s", notif["message"][:80])
        return {"status": "QUEUED", "channel": "email"}

    def _send_whatsapp(self, notif):
        logger.info("[Notifications] WhatsApp queued: %s", notif["message"][:80])
        return {"status": "QUEUED", "channel": "whatsapp"}

    def _send_slack(self, notif):
        url = os.getenv("SLACK_WEBHOOK_URL")
        if url:
            try:
                import httpx
                httpx.post(url, json={"text": "[{}] {} - {}".format(notif["severity"], notif["event"], notif["message"])}, timeout=10)
                return {"status": "SENT", "channel": "slack"}
            except Exception as e:
                return {"status": "FAILED", "error": str(e)}
        return {"status": "NOT_CONFIGURED"}

    def _send_teams(self, notif):
        url = os.getenv("TEAMS_WEBHOOK_URL")
        if url:
            try:
                import httpx
                httpx.post(url, json={"text": "[{}] {} - {}".format(notif["severity"], notif["event"], notif["message"])}, timeout=10)
                return {"status": "SENT", "channel": "teams"}
            except Exception as e:
                return {"status": "FAILED", "error": str(e)}
        return {"status": "NOT_CONFIGURED"}

    def _send_telegram(self, notif):
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if token and chat_id:
            try:
                import httpx
                httpx.post("https://api.telegram.org/bot{}/sendMessage".format(token), json={"chat_id": chat_id, "text": "[{}] {} - {}".format(notif["severity"], notif["event"], notif["message"])}, timeout=10)
                return {"status": "SENT", "channel": "telegram"}
            except Exception as e:
                return {"status": "FAILED", "error": str(e)}
        return {"status": "NOT_CONFIGURED"}

    def _send_webhook(self, notif):
        url = os.getenv("NOTIFICATION_WEBHOOK_URL")
        if url:
            try:
                import httpx
                httpx.post(url, json=notif, timeout=10)
                return {"status": "SENT", "channel": "webhook"}
            except Exception as e:
                return {"status": "FAILED", "error": str(e)}
        return {"status": "NOT_CONFIGURED"}

    def get_status(self):
        active = [k for k, v in self._channels.items() if v["enabled"]]
        return {
            "version": self.version,
            "channels_active": active,
            "channels_total": len(self._channels),
            "queue_size": len(self._queue),
            "total_sent": len(self._sent),
            "recent": list(self._sent)[-10:],
        }

notification_center = NotificationCenter()