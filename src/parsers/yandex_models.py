import datetime
from typing import Optional

from pydantic import BaseModel
from yandex_ai_studio_sdk._search_api.web.result import WebSearchDocument


class WEBSearchResult(BaseModel):
    title: str
    lang: str
    target_domain: Optional[str]
    target_url: Optional[str]
    ts: datetime.datetime
    mime: str
    text: str

    @staticmethod
    def from_yandex(doc: WebSearchDocument) -> 'WEBSearchResult':
        text = '\n'.join(doc.passages)
        props = doc.extra.get("properties", dict())
        if ext_text := props.get("extended-text", None):
            text += "\n" + ext_text
        return WEBSearchResult(
            title=doc.title,
            lang=doc.lang or 'ru',
            target_domain=doc.domain,
            target_url=doc.url,
            ts=doc.modtime or datetime.datetime.now(),
            mime=doc.extra.get("mime-type", "text/html"),
            text=text
        )
