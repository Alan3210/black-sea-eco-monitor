from typing import Optional

from pydantic import BaseModel


class NewsItem(BaseModel):

    title: str

    url: str

    source: str

    published_at: Optional[str] = None

    summary: Optional[str] = None