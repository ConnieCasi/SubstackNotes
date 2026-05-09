import requests


class SubstackClient:
    POST_NOTE_URL = "https://substack.com/api/v1/comment/feed"

    def __init__(self, session_cookie: str):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.cookies.set("substack.sid", session_cookie, domain=".substack.com")

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
        resp.raise_for_status()
        return resp.json()
