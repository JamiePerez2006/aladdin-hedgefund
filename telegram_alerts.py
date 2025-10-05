# telegram_alerts.py
import os, requests, time

TELEGRAM_BASE = "https://api.telegram.org/bot{token}/{method}"

class Alerts:
    """
    Einfache Telegram-Alerts:
      - Alerts.from_streamlit_secrets(st.secrets)  -> nutzt Streamlit Secrets
      - send(text)  -> normaler Alarm
      - send_once_per_min(key, text) -> Rate Limit (pro key/min)
    """

    def __init__(self, bot_token: str | None, chat_id: str | None):
        self.token = (bot_token or "").strip()
        self.chat_id = (chat_id or "").strip()
        self._last_sent = {}

    @classmethod
    def from_streamlit_secrets(cls, secrets):
        # liest aus Streamlit Cloud: st.secrets["TELEGRAM_BOT_TOKEN"], st.secrets["TELEGRAM_CHAT_ID"]
        t = secrets.get("TELEGRAM_BOT_TOKEN", "")
        c = secrets.get("TELEGRAM_CHAT_ID", "")
        return cls(t, c)

    @classmethod
    def from_env(cls):
        return cls(os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID"))

    def configured(self) -> bool:
        return bool(self.token) and bool(self.chat_id)

    def _post(self, method: str, payload: dict):
        if not self.configured():
            return False, "Telegram not configured"
        try:
            url = TELEGRAM_BASE.format(token=self.token, method=method)
            r = requests.post(url, json=payload, timeout=10)
            ok = r.status_code == 200 and r.json().get("ok", False)
            return ok, ("" if ok else r.text)
        except Exception as e:
            return False, str(e)

    def send(self, text: str, disable_notification: bool = False):
        payload = {"chat_id": self.chat_id, "text": text, "disable_notification": disable_notification}
        return self._post("sendMessage", payload)

    def send_once_per_min(self, key: str, text: str):
        now = int(time.time())
        last = self._last_sent.get(key, 0)
        if now - last < 60:
            return False, "rate-limited"
        self._last_sent[key] = now
        return self.send(text)
