from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import AIReport, User
from app.schemas.ai import AIAnalysisRequest, AIReportOut, ResumeBulletsRequest
from app.services.ai_service import generate_ai_report, generate_resume_bullets

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/career-analysis", response_model=AIReportOut)
def career_analysis(
    payload: AIAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return generate_ai_report(db, current_user.id, payload.target_role)


@router.post("/resume-bullets", response_model=AIReportOut)
def resume_bullets(
    payload: ResumeBulletsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Turns the user's strongest synced repos into ready-to-paste resume
    bullet points for a target role, in a chosen tone."""
    return generate_resume_bullets(db, current_user.id, payload.target_role, payload.tone)


@router.get("/reports", response_model=list[AIReportOut])
def reports(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(AIReport)
        .filter(AIReport.user_id == current_user.id)
        .order_by(AIReport.created_at.desc())
        .all()
    )
