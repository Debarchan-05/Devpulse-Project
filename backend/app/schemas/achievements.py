from datetime import datetime

from pydantic import BaseModel


class BadgeOut(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    earned: bool = False
    earned_at: datetime | None = None

    model_config = {"from_attributes": True}
