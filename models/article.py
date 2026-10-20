from datetime import datetime
from pydantic import BaseModel, HttpUrl

class Article(BaseModel):
    title: str
    url: HttpUrl
    content: str | None = None
    published_at: datetime | None = None
