import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.prediction_history import PredictionHistory
from app.models.user import User, UserRole


@pytest.fixture
def patient_user_a():
    with SessionLocal() as db:
        user = User(
            email="patient_a@example.com",
            full_name="Patient Alice",
            hashed_password=hash_password("PasswordAlice123!"),
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    yield user

    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()


@pytest.fixture
def patient_user_b():
    with SessionLocal() as db:
        user = User(
            email="patient_b@example.com",
            full_name="Patient Bob",
            hashed_password=hash_password("PasswordBob123!"),
            role=UserRole.PATIENT,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    yield user

    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()


@pytest.fixture
def doctor_user():
    with SessionLocal() as db:
        user = User(
            email="doctor_history@example.com",
            full_name="Dr. History",
            hashed_password=hash_password("PasswordDoc123!"),
            role=UserRole.DOCTOR,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    yield user

    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()


@pytest.fixture
def researcher_user():
    with SessionLocal() as db:
        user = User(
            email="researcher_history@example.com",
            full_name="Dr. Researcher",
            hashed_password=hash_password("PasswordRes123!"),
            role=UserRole.RESEARCHER,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    yield user

    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()


@pytest.fixture
def sample_record_a(patient_user_a):
    record_uuid = str(uuid.uuid4())
    with SessionLocal() as db:
        rec = PredictionHistory(
            record_id=record_uuid,
            user_id=patient_user_a.id,
            condition="heart",
            predicted_label="Elevated Risk",
            predicted_positive=True,
            probability=0.78,
            threshold=0.5,
            aggregation_method="majority_voting",
            model_version="heart-20261010T095400Z",
            is_experimental=True,
            model_results=[
                {
                    "model_name": "random_forest",
                    "probability": 0.78,
                    "predicted_positive": True,
                    "threshold": 0.5,
                    "status": "success",
                },
                {
                    "model_name": "logistic_regression",
                    "probability": 0.72,
                    "predicted_positive": True,
                    "threshold": 0.5,
                    "status": "success",
                },
                {
                    "model_name": "gradient_boosting",
                    "probability": 0.81,
                    "predicted_positive": True,
                    "threshold": 0.5,
                    "status": "success",
                },
                {
                    "model_name": "mlp",
                    "probability": 0.65,
                    "predicted_positive": True,
                    "threshold": 0.5,
                    "status": "success",
                },
            ],
            top_factors=[
                {
                    "feature": "ca",
                    "label": "Major vessels",
                    "value": 2.0,
                    "contribution": 0.25,
                    "imputed": False,
                },
                {
                    "feature": "chol",
                    "label": "Cholesterol",
                    "value": 260.0,
                    "contribution": 0.12,
                    "imputed": False,
                },
            ],
            input_summary={"age": 55, "chol": 260, "trestbps": 140},
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

    yield rec

    with SessionLocal() as db:
        stmt = select(PredictionHistory).where(PredictionHistory.record_id == record_uuid)
        r = db.scalars(stmt).first()
        if r:
            db.delete(r)
            db.commit()


def test_patient_can_only_see_own_history(patient_user_a, patient_user_b, sample_record_a):
    token_a = create_access_token(subject=patient_user_a.id)
    token_b = create_access_token(subject=patient_user_b.id)

    with TestClient(app) as client:
        # Patient A sees their record
        res_a = client.get(
            "/api/v1/history",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_a.status_code == 200
        data_a = res_a.json()
        assert data_a["total"] >= 1
        record_ids_a = [item["record_id"] for item in data_a["items"]]
        assert sample_record_a.record_id in record_ids_a

        # Patient B has empty history
        res_b = client.get(
            "/api/v1/history",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_b.status_code == 200
        data_b = res_b.json()
        assert data_b["total"] == 0
        assert len(data_b["items"]) == 0


def test_patient_cannot_access_other_patient_record_detail(
    patient_user_a, patient_user_b, sample_record_a
):
    token_a = create_access_token(subject=patient_user_a.id)
    token_b = create_access_token(subject=patient_user_b.id)

    with TestClient(app) as client:
        # Patient A accesses own detail -> 200
        res_a = client.get(
            f"/api/v1/history/{sample_record_a.record_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res_a.status_code == 200
        assert res_a.json()["record_id"] == sample_record_a.record_id
        assert res_a.json()["condition"] == "heart"

        # Patient B attempts to access Patient A's record -> 403 Forbidden
        res_b = client.get(
            f"/api/v1/history/{sample_record_a.record_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res_b.status_code == 403
        assert "permission" in res_b.json()["detail"].lower()


def test_doctor_can_access_record_detail(doctor_user, sample_record_a):
    doc_token = create_access_token(subject=doctor_user.id)
    with TestClient(app) as client:
        res = client.get(
            f"/api/v1/history/{sample_record_a.record_id}",
            headers={"Authorization": f"Bearer {doc_token}"},
        )
        assert res.status_code == 200
        assert res.json()["record_id"] == sample_record_a.record_id


def test_history_record_not_found(patient_user_a):
    token_a = create_access_token(subject=patient_user_a.id)
    non_existent_uuid = str(uuid.uuid4())
    with TestClient(app) as client:
        res = client.get(
            f"/api/v1/history/{non_existent_uuid}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 404


def test_pdf_download_authorized_and_returns_valid_pdf(patient_user_a, sample_record_a):
    token_a = create_access_token(subject=patient_user_a.id)
    with TestClient(app) as client:
        res = client.get(
            f"/api/v1/history/{sample_record_a.record_id}/pdf",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert "attachment" in res.headers["content-disposition"]
        expected_name = f"claridx_heart_{sample_record_a.record_id[:8]}.pdf"
        assert expected_name in res.headers["content-disposition"]
        assert res.content.startswith(b"%PDF-")


def test_pdf_download_forbidden_for_other_patient(patient_user_b, sample_record_a):
    token_b = create_access_token(subject=patient_user_b.id)
    with TestClient(app) as client:
        res = client.get(
            f"/api/v1/history/{sample_record_a.record_id}/pdf",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert res.status_code == 403


def test_researcher_cannot_access_history_endpoints(researcher_user, sample_record_a):
    token = create_access_token(subject=researcher_user.id)
    with TestClient(app) as client:
        # Cannot list history
        res_list = client.get(
            "/api/v1/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_list.status_code == 403
        assert "not enough permissions" in res_list.json()["detail"].lower()

        # Cannot view detail
        res_detail = client.get(
            f"/api/v1/history/{sample_record_a.record_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_detail.status_code == 403
        assert "not enough permissions" in res_detail.json()["detail"].lower()

        # Cannot download PDF
        res_pdf = client.get(
            f"/api/v1/history/{sample_record_a.record_id}/pdf",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res_pdf.status_code == 403
        assert "not enough permissions" in res_pdf.json()["detail"].lower()


def test_history_timestamp_serialization_is_iso8601_utc(patient_user_a, sample_record_a):
    token_a = create_access_token(subject=patient_user_a.id)
    with TestClient(app) as client:
        res = client.get(
            f"/api/v1/history/{sample_record_a.record_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "created_at" in data
        created_str = data["created_at"]
        # Must end with +00:00 or Z indicating timezone awareness
        assert created_str.endswith("+00:00") or created_str.endswith("Z")
        # Must be parseable as ISO 8601
        from datetime import datetime

        dt = datetime.fromisoformat(created_str)
        assert dt.tzinfo is not None


def test_pdf_report_contains_timestamp_and_patient_guidance(patient_user_a, sample_record_a):
    import base64
    import re
    import zlib

    token_a = create_access_token(subject=patient_user_a.id)
    with TestClient(app) as client:
        res = client.get(
            f"/api/v1/history/{sample_record_a.record_id}/pdf",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        pdf_bytes = res.content
        assert pdf_bytes.startswith(b"%PDF-")
        decompressed_streams = []
        for m in re.finditer(b"stream", pdf_bytes):
            start = pdf_bytes.find(b"\n", m.start()) + 1
            end = pdf_bytes.find(b"endstream", start)
            raw_stream = pdf_bytes[start:end].strip()
            try:
                decompressed = zlib.decompress(base64.a85decode(raw_stream, adobe=True))
                dec = decompressed.decode("latin1", errors="ignore")
                decompressed_streams.append(dec)
            except Exception:
                pass
        combined = " ".join(decompressed_streams)
        assert "UTC" in combined
        assert "Patient Interpretation" in combined
        assert "What to do next" in combined


def test_pdf_report_elevated_risk_exact_patient_guidance(patient_user_a, sample_record_a):
    import base64
    import re
    import zlib

    token_a = create_access_token(subject=patient_user_a.id)
    with TestClient(app) as client:
        res = client.get(
            f"/api/v1/history/{sample_record_a.record_id}/pdf",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        pdf_bytes = res.content
        decompressed_streams = []
        for m in re.finditer(b"stream", pdf_bytes):
            start = pdf_bytes.find(b"\n", m.start()) + 1
            end = pdf_bytes.find(b"endstream", start)
            raw_stream = pdf_bytes[start:end].strip()
            try:
                decompressed = zlib.decompress(base64.a85decode(raw_stream, adobe=True))
                dec = decompressed.decode("latin1", errors="ignore")
                decompressed_streams.append(dec)
            except Exception:
                pass
        combined = " ".join(decompressed_streams)
        joined_text = " ".join(re.findall(r"\((.*?)\)\s*Tj", combined))

        # Verify exact substantive guidance text for elevated risk
        assert (
            "statistical pattern associated with elevated risk in retrospective research data"
            in joined_text
        )
        assert (
            "decision-support estimate based solely on the measurements provided,"
            " not a clinical diagnosis" in joined_text
        )
        assert "Share this report with your qualified healthcare provider" in joined_text
        assert (
            "licensed clinician must evaluate these indicators in the context of"
            " your complete medical history" in joined_text
        )
        assert "Do not start, stop, or alter any medications or treatments" in joined_text
        assert "acute symptoms, seek immediate emergency care" in joined_text
        # Primary model attribution
        assert "Random Forest" in joined_text
        # UTC label
        assert "Assessment Timestamp \\(UTC\\):" in joined_text
        assert "UTC" in joined_text


def test_pdf_report_lower_risk_exact_patient_guidance(patient_user_a):
    import base64
    import re
    import zlib

    # Create lower-risk diabetes record
    record_uuid = str(uuid.uuid4())
    with SessionLocal() as db:
        rec = PredictionHistory(
            record_id=record_uuid,
            user_id=patient_user_a.id,
            condition="diabetes",
            predicted_label="Lower Risk",
            predicted_positive=False,
            probability=0.18,
            threshold=0.5,
            aggregation_method="majority_voting",
            model_version="diabetes-20261010T095400Z",
            is_experimental=True,
            model_results=[
                {
                    "model_name": "random_forest",
                    "probability": 0.18,
                    "predicted_positive": False,
                    "threshold": 0.5,
                    "status": "success",
                },
                {
                    "model_name": "logistic_regression",
                    "probability": 0.22,
                    "predicted_positive": False,
                    "threshold": 0.5,
                    "status": "success",
                },
                {
                    "model_name": "gradient_boosting",
                    "probability": 0.15,
                    "predicted_positive": False,
                    "threshold": 0.5,
                    "status": "success",
                },
                {
                    "model_name": "mlp",
                    "probability": 0.25,
                    "predicted_positive": False,
                    "threshold": 0.5,
                    "status": "success",
                },
            ],
            top_factors=[
                {
                    "feature": "plas",
                    "label": "Glucose",
                    "value": 90.0,
                    "contribution": -0.42,
                    "imputed": False,
                },
                {
                    "feature": "mass",
                    "label": "BMI",
                    "value": 22.4,
                    "contribution": -0.28,
                    "imputed": False,
                },
            ],
            input_summary={"glu": 90, "bmi": 22.4},
        )
        db.add(rec)
        db.commit()

    token_a = create_access_token(subject=patient_user_a.id)
    with TestClient(app) as client:
        res = client.get(
            f"/api/v1/history/{record_uuid}/pdf",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        pdf_bytes = res.content
        decompressed_streams = []
        for m in re.finditer(b"stream", pdf_bytes):
            start = pdf_bytes.find(b"\n", m.start()) + 1
            end = pdf_bytes.find(b"endstream", start)
            raw_stream = pdf_bytes[start:end].strip()
            try:
                decompressed = zlib.decompress(base64.a85decode(raw_stream, adobe=True))
                dec = decompressed.decode("latin1", errors="ignore")
                decompressed_streams.append(dec)
            except Exception:
                pass
        combined = " ".join(decompressed_streams)
        joined_text = " ".join(re.findall(r"\((.*?)\)\s*Tj", combined))

        # Verify exact substantive guidance text for lower risk
        assert (
            "evaluated models did not detect elevated risk patterns in your submitted measurements"
            in joined_text
        )
        assert "informational indicator, not a definitive diagnosis or a guarantee" in joined_text
        assert "Share this report with your qualified healthcare provider" in joined_text
        # Primary model attribution
        assert "Random Forest" in joined_text
        # Ensure other users' data or passwords are not exposed
        assert "Password" not in joined_text
        assert "hashed_password" not in joined_text

    with SessionLocal() as db:
        r = db.get(PredictionHistory, record_uuid)
        if r:
            db.delete(r)
            db.commit()
