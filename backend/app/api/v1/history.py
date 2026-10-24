from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import func, select

from app.api.deps import DbDep, PredictionUserDep
from app.models.prediction_history import PredictionHistory
from app.models.user import UserRole
from app.schemas.history import HistoryListResponse, HistoryRecordOut
from app.services.pdf_generator import generate_prediction_pdf

router = APIRouter(prefix="/history", tags=["prediction history"])


@router.get("", response_model=HistoryListResponse)
def list_history(
    current_user: PredictionUserDep,
    db: DbDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    condition: str | None = Query(default=None),
) -> HistoryListResponse:
    """Retrieve paginated prediction history.

    Patients can only view their own prediction records.
    Doctors and administrators can view history across patients.
    """
    stmt = select(PredictionHistory)
    count_stmt = select(func.count(PredictionHistory.id))

    if current_user.role == UserRole.PATIENT:
        stmt = stmt.where(PredictionHistory.user_id == current_user.id)
        count_stmt = count_stmt.where(PredictionHistory.user_id == current_user.id)

    if condition:
        cond_clean = condition.strip().lower()
        stmt = stmt.where(PredictionHistory.condition == cond_clean)
        count_stmt = count_stmt.where(PredictionHistory.condition == cond_clean)

    total = db.scalar(count_stmt) or 0
    records = db.scalars(
        stmt.order_by(PredictionHistory.created_at.desc()).offset(offset).limit(limit)
    ).all()

    return HistoryListResponse(
        items=[HistoryRecordOut.model_validate(r) for r in records],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{record_id}", response_model=HistoryRecordOut)
def get_history_detail(
    record_id: str,
    current_user: PredictionUserDep,
    db: DbDep,
) -> HistoryRecordOut:
    """Retrieve detailed prediction record by UUID.

    Enforces ownership: Patients can only view records they created.
    """
    record = db.scalars(
        select(PredictionHistory).where(PredictionHistory.record_id == record_id)
    ).first()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction record not found",
        )

    if current_user.role == UserRole.PATIENT and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this prediction record",
        )

    return HistoryRecordOut.model_validate(record)


@router.get("/{record_id}/pdf")
def download_history_pdf(
    record_id: str,
    current_user: PredictionUserDep,
    db: DbDep,
) -> Response:
    """Generate and download a validated clinical decision support PDF report.

    Enforces ownership: Patients can only download their own reports.
    """
    record = db.scalars(
        select(PredictionHistory).where(PredictionHistory.record_id == record_id)
    ).first()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction record not found",
        )

    if current_user.role == UserRole.PATIENT and record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to download this report",
        )

    pdf_bytes = generate_prediction_pdf(record)
    filename = f"claridx_{record.condition}_{record.record_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
