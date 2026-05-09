import requests
from urllib.parse import unquote


class SubstackClient:
    POST_NOTE_URL = "https://substack.com/api/v1/comment/feed"

    def __init__(self, session_cookie: str):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        })
        self.session.cookies.set("substack.sid", unquote(session_cookie), domain=".substack.com")

    @staticmethod
    def _text_to_prosemirror(text: str) -> list:
        content = []
        for line in text.split("\n"):
            if line.strip():
                content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": line}],
                })
            else:
                content.append({"type": "paragraph"})
        return content

    def post_note(self, text: str) -> dict:
        body = {
            "bodyJson": {
                "type": "doc",
                "attrs": {"schemaVersion": "v1"},
                "content": self._text_to_prosemirror(text),
            },
            "tabId": "for-you",
            "replyMinimumRole": "everyone",
        }

        resp = self.session.post(self.POST_NOTE_URL, json=body)
        if not resp.ok:
            print(f"HTTP {resp.status_code}: {resp.text[:500]}")
            resp.raise_for_status()
        return resp.json()
