import json

from fastapi import HTTPException
from openai import OpenAI
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import AIReport, DeveloperMetric, Repository


def _get_client() -> OpenAI:
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.openai_api_key)


def _load_profile(db: Session, user_id: int, target_role: str) -> dict:
    metric = (
        db.query(DeveloperMetric)
        .filter(DeveloperMetric.user_id == user_id)
        .order_by(DeveloperMetric.created_at.desc())
        .first()
    )
    repos = db.query(Repository).filter(Repository.user_id == user_id).all()
    if not metric:
        raise HTTPException(status_code=400, detail="Sync a GitHub profile before requesting AI analysis")

    return {
        "target_role": target_role,
        "developer_score": metric.overall_score,
        "coding": metric.coding_score,
        "project": metric.project_score,
        "testing": metric.testing_score,
        "documentation": metric.documentation_score,
        "activity": metric.activity_score,
        "diversity": metric.diversity_score,
        "repositories": [
            {
                "name": r.name,
                "language": r.language,
                "stars": r.stars,
                "description": r.description,
                "topics": r.topics,
                "repo_health_score": r.repo_health_score,
            }
            for r in sorted(repos, key=lambda r: r.stars, reverse=True)[:20]
        ],
    }


def _save_report(db: Session, user_id: int, report_type: str, content: str) -> AIReport:
    report = AIReport(user_id=user_id, report_type=report_type, content=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def generate_ai_report(db: Session, user_id: int, target_role: str) -> AIReport:
    client = _get_client()
    profile = _load_profile(db, user_id, target_role)

    prompt = f"""You are the career analyst inside DevPulse.
Analyze this developer profile for the target role and return a concise, practical report.
Do not invent facts. Use only the supplied metrics and repository metadata.

Profile:
{json.dumps(profile, indent=2)}

Return:
1. Strengths (3 bullets)
2. Weaknesses (3 bullets)
3. Skill gaps for the target role (up to 5)
4. A 4-step learning roadmap
5. Three concrete improvements to the existing GitHub profile
"""

    try:
        response = client.responses.create(
            model=settings.openai_model,
            instructions="You are a practical software-career mentor. Be specific and honest.",
            input=prompt,
        )
        content = response.output_text
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {exc}") from exc

    return _save_report(db, user_id, "CAREER_ANALYSIS", content)


def generate_resume_bullets(db: Session, user_id: int, target_role: str, tone: str) -> AIReport:
    """
    A separate, more narrowly-scoped AI feature from career-analysis:
    turns the developer's strongest repos into 4-6 ATS-friendly resume
    bullet points for a specific target role and tone. Kept as its own
    endpoint/report_type so the two AI features can evolve independently
    and so /ai/reports shows a clear history of each.
    """
    client = _get_client()
    profile = _load_profile(db, user_id, target_role)

    tone_hint = {
        "professional": "Formal, polished language suitable for a corporate resume.",
        "concise": "Very short, punchy bullets -- no more than 12 words each.",
        "impact": "Lead every bullet with a strong action verb and, where the data supports it, a quantified outcome (stars, forks, repo count).",
    }[tone]

    prompt = f"""You write resume bullet points for software developers applying for: {target_role}.
Tone: {tone_hint}
Only use facts present in this profile -- never invent metrics, employers, or outcomes.

Profile:
{json.dumps(profile, indent=2)}

Return 4 to 6 resume bullet points as a plain bulleted list. No preamble, no closing remarks.
"""

    try:
        response = client.responses.create(
            model=settings.openai_model,
            instructions="You are an expert technical resume writer. Be truthful and specific.",
            input=prompt,
        )
        content = response.output_text
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI provider request failed: {exc}") from exc

    return _save_report(db, user_id, "RESUME_BULLETS", content)
