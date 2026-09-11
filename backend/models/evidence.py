from pydantic import BaseModel
from typing import Optional

from backend.models.source import Source


class Evidence(BaseModel):

    type: str

    description: str

    confidence: float

    source: Optional[Source] = None