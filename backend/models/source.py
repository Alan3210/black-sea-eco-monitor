from pydantic import BaseModel
from typing import Optional


class Source(BaseModel):

    type: str

    name: str

    url: Optional[str] = None

    reliability: float = 0.5