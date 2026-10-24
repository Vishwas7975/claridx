import html
from datetime import UTC
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.models.prediction_history import PredictionHistory


def generate_prediction_pdf(record: PredictionHistory) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "DocBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#64748b"),
    )

    story = []

    # Header
    story.append(Paragraph("ClariDx &mdash; Clinical Decision Support Report", title_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Explainable AI Decision Support System &bull; Transparent Risk Estimation",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 10))
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#0284c7"),
            spaceAfter=14,
        )
    )

    # Assessment Meta Table
    cond_name = "Heart Disease Risk" if record.condition == "heart" else "Type 2 Diabetes Risk"
    if record.created_at:
        dt = record.created_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        created_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        created_str = "N/A"
    outcome_label = (
        "Elevated Risk Detected" if record.predicted_positive else "Lower Risk Indicated"
    )
    outcome_color = "#b91c1c" if record.predicted_positive else "#15803d"
    exp_suffix = "Experimental" if record.is_experimental else "Validated"

    meta_data = [
        [
            Paragraph("<b>Record ID:</b>", body_style),
            Paragraph(html.escape(record.record_id), body_style),
            Paragraph("<b>Assessment Timestamp (UTC):</b>", body_style),
            Paragraph(html.escape(created_str), body_style),
        ],
        [
            Paragraph("<b>Condition:</b>", body_style),
            Paragraph(html.escape(cond_name), body_style),
            Paragraph("<b>Outcome:</b>", body_style),
            Paragraph(f"<font color='{outcome_color}'><b>{outcome_label}</b></font>", body_style),
        ],
        [
            Paragraph("<b>Probability:</b>", body_style),
            Paragraph(f"{record.probability:.1%}", body_style),
            Paragraph("<b>Threshold:</b>", body_style),
            Paragraph(f"{record.threshold:.2f}", body_style),
        ],
        [
            Paragraph("<b>Method:</b>", body_style),
            Paragraph(
                html.escape(f"{record.aggregation_method} ({exp_suffix})"),
                body_style,
            ),
            Paragraph("<b>Model Version:</b>", body_style),
            Paragraph(html.escape(record.model_version or "N/A"), body_style),
        ],
    ]

    meta_table = Table(meta_data, colWidths=[90, 180, 100, 160])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # All 4 Models Execution Summary
    if record.model_results:
        story.append(Paragraph("Multi-Model Evaluation Summary", heading_style))
        story.append(
            Paragraph(
                "ClariDx executes four independent machine learning classifiers to assess "
                "across different mathematical paradigms. Results are compared using majority "
                "voting.",
                body_style,
            )
        )
        story.append(Spacer(1, 6))

        model_headers = [
            Paragraph("<b>Model Architecture</b>", body_style),
            Paragraph("<b>Status</b>", body_style),
            Paragraph("<b>Raw Score</b>", body_style),
            Paragraph("<b>Indication</b>", body_style),
        ]
        model_rows = [model_headers]

        name_display = {
            "random_forest": "Random Forest (Tree Ensemble)",
            "logistic_regression": "Logistic Regression (Linear Reference)",
            "gradient_boosting": "Gradient Boosting (Boosted Trees)",
            "mlp": "Multi-Layer Perceptron (Neural Net)",
        }

        for m in record.model_results:
            m_name = name_display.get(m.get("model_name"), m.get("model_name", "Unknown"))
            m_status = m.get("status", "success")
            m_prob = f"{m['probability']:.1%}" if m.get("probability") is not None else "N/A"
            m_ind = (
                "Elevated Risk"
                if m.get("predicted_positive")
                else ("Lower Risk" if m.get("predicted_positive") is not None else "Failed")
            )
            model_rows.append(
                [
                    Paragraph(html.escape(m_name), body_style),
                    Paragraph(html.escape(m_status.title()), body_style),
                    Paragraph(html.escape(m_prob), body_style),
                    Paragraph(html.escape(m_ind), body_style),
                ]
            )

        models_table = Table(model_rows, colWidths=[200, 80, 100, 150])
        models_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(models_table)
        story.append(Spacer(1, 14))

    # Top Influential Factors Table
    if record.top_factors:
        story.append(Paragraph("Key Explanatory Factors (SHAP Analysis)", heading_style))
        story.append(
            Paragraph(
                "The primary validated model identifies the following physiological measurements "
                "as having the strongest mathematical influence on this risk assessment:",
                body_style,
            )
        )
        story.append(Spacer(1, 6))

        factor_headers = [
            Paragraph("<b>Clinical Factor</b>", body_style),
            Paragraph("<b>Value</b>", body_style),
            Paragraph("<b>Direction</b>", body_style),
            Paragraph("<b>Contribution</b>", body_style),
        ]
        factor_rows = [factor_headers]

        for f in record.top_factors[:6]:
            label = f.get("label", f.get("feature", ""))
            val = str(f.get("value")) if f.get("value") is not None else "Missing"
            contrib = f.get("contribution", 0.0)
            direction = "Increases Risk" if contrib > 0 else "Decreases Risk"
            factor_rows.append(
                [
                    Paragraph(html.escape(label), body_style),
                    Paragraph(html.escape(val), body_style),
                    Paragraph(html.escape(direction), body_style),
                    Paragraph(f"{contrib:+.4f}", body_style),
                ]
            )

        factors_table = Table(factor_rows, colWidths=[200, 90, 120, 120])
        factors_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        story.append(factors_table)
        story.append(Spacer(1, 16))

    # Patient Interpretation & Recommended Next Steps
    story.append(Paragraph("Patient Interpretation &amp; Next Steps", heading_style))
    if record.predicted_positive:
        means_text = (
            "This assessment reflects a statistical pattern associated with elevated risk in "
            "retrospective research data. It is an experimental decision-support estimate based "
            "solely on the measurements provided, not a clinical diagnosis or medical conclusion."
        )
    else:
        means_text = (
            "The evaluated models did not detect elevated risk patterns in your submitted "
            "measurements relative to the training baseline. This is an informational indicator, "
            "not a definitive diagnosis or a guarantee against underlying conditions."
        )

    next_steps_text = (
        "Share this report with your qualified healthcare provider. A licensed clinician "
        "must evaluate these indicators in the context of your complete medical history, "
        "physical symptoms, and confirmatory laboratory tests. Do not start, stop, or alter "
        "any medications or treatments based solely on an automated AI risk score. "
        "If you experience acute symptoms, seek immediate emergency care."
    )
    interpretation_text = (
        f"<b>What this result means:</b> {means_text}<br/><b>What to do next:</b> {next_steps_text}"
    )
    story.append(Paragraph(interpretation_text, body_style))
    story.append(Spacer(1, 14))

    # Disclaimer & Limitations
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#94a3b8"),
            spaceAfter=8,
        )
    )
    story.append(
        Paragraph("<b>IMPORTANT CLINICAL SAFETY NOTICE &amp; LIMITATIONS</b>", disclaimer_style)
    )
    story.append(Spacer(1, 4))
    disclaimer_text = (
        "This report is produced by ClariDx, an experimental academic clinical decision-support "
        "prototype. It is <b>NOT A MEDICAL DIAGNOSIS</b>, clinical recommendation, or treatment "
        "prescription. The underlying models were trained on retrospective research cohorts "
        "(Cleveland Heart Disease, Pima Indians Diabetes) and have not been cleared by "
        "regulatory bodies for autonomous diagnostic use. Model outputs are statistical "
        "estimates and raw probability scores are uncalibrated. Patients must share this "
        "summary with a qualified healthcare professional for clinical correlation, diagnostic "
        "testing, and individualized medical decisions."
    )
    story.append(Paragraph(disclaimer_text, disclaimer_style))

    doc.build(story)
    return buf.getvalue()
