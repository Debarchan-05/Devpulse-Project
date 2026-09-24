from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import User
from app.schemas.achievements import BadgeOut
from app.services.badge_service import get_badge_board

router = APIRouter(prefix="/achievements", tags=["Achievements"])


@router.get("", response_model=list[BadgeOut])
def list_achievements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Full Pulse Badge catalog, each flagged with whether (and when) the
    current user has earned it. Badges are awarded automatically inside
    POST /github/sync -- there's nothing to claim manually."""
    return get_badge_board(db, current_user.id)
