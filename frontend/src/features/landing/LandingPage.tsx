import { useState } from 'react'
import { ThemeToggle } from '../../components/ThemeToggle'

interface LandingPageProps {
  onNavigate: (view: 'login' | 'register' | 'request-access') => void
}

export function LandingPage({ onNavigate }: LandingPageProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [activeTabDemo, setActiveTabDemo] = useState<'heart' | 'diabetes'>('heart')

  const scrollToSection = (id: string) => {
    setMobileMenuOpen(false)
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <div className="landing-root">
      {/* ===== Global Navigation Header ===== */}
      <header className="landing-header">
        <div className="container header-inner">
          <div
            className="brand"
            onClick={() => scrollToSection('hero')}
            style={{ cursor: 'pointer' }}
          >
            <div className="brand-mark" aria-hidden="true">
              Cx
            </div>
            <div className="brand-text">
              <h1 className="brand-name">ClariDx</h1>
              <span className="brand-tagline">Clinical AI you can see through</span>
            </div>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="landing-nav-links" aria-label="Landing page sections">
            <button
              type="button"
              className="nav-link-btn"
              onClick={() => scrollToSection('pipeline')}
            >
              How It Works
            </button>
            <button
              type="button"
              className="nav-link-btn"
              onClick={() => scrollToSection('conditions')}
            >
              Conditions
            </button>
            <button
              type="button"
              className="nav-link-btn"
              onClick={() => scrollToSection('explainability')}
            >
              Explainability
            </button>
            <button
              type="button"
              className="nav-link-btn"
              onClick={() => scrollToSection('reports')}
            >
              Reports
            </button>
            <button
              type="button"
              className="nav-link-btn"
              onClick={() => scrollToSection('safety')}
            >
              Safety
            </button>
          </nav>

          {/* Top Actions & Theme Toggle */}
          <div className="landing-nav-actions">
            <ThemeToggle />
            <button type="button" className="btn-signin-nav" onClick={() => onNavigate('login')}>
              Sign In
            </button>
            <button
              type="button"
              className="btn-signup-nav primary"
              onClick={() => onNavigate('register')}
            >
              Get Started
            </button>

            {/* Mobile Hamburger Button */}
            <button
              type="button"
              className="mobile-menu-toggle"
              aria-label={mobileMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={mobileMenuOpen}
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                {mobileMenuOpen ? (
                  <path d="M18 6L6 18M6 6l12 12" />
                ) : (
                  <path d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && (
          <div className="landing-mobile-menu">
            <button
              type="button"
              className="mobile-link"
              onClick={() => scrollToSection('pipeline')}
            >
              How It Works
            </button>
            <button
              type="button"
              className="mobile-link"
              onClick={() => scrollToSection('conditions')}
            >
              Conditions
            </button>
            <button
              type="button"
              className="mobile-link"
              onClick={() => scrollToSection('explainability')}
            >
              Explainability
            </button>
            <button
              type="button"
              className="mobile-link"
              onClick={() => scrollToSection('reports')}
            >
              Reports
            </button>
            <button type="button" className="mobile-link" onClick={() => scrollToSection('safety')}>
              Safety
            </button>
            <div className="mobile-actions">
              <button
                type="button"
                className="btn-signin-nav w-full"
                onClick={() => onNavigate('login')}
              >
                Sign In
              </button>
              <button
                type="button"
                className="btn-signup-nav primary w-full"
                onClick={() => onNavigate('register')}
              >
                Get Started
              </button>
            </div>
          </div>
        )}
      </header>

      {/* ===== Permanent Clinical Research Banner ===== */}
      <div className="disclaimer-banner" role="note">
        Research prototype for decision support and education only. It is not a medical device and
        must not be used for diagnosis or treatment.
      </div>

      <main className="landing-main">
        {/* ===== Hero Section ===== */}
        <section id="hero" className="hero-section">
          <div className="container hero-container">
            <div className="hero-content">
              <div className="hero-badge">
                <span className="badge-dot" aria-hidden="true" />
                <span>Explainable AI • Multi-Model Consensus • Transparent Healthcare</span>
              </div>
              <h1 className="hero-title">
                Clinical AI Decision Support{' '}
                <span className="highlight-text">You Can See Through</span>
              </h1>
              <p className="hero-lead">
                ClariDx evaluates cardiovascular and diabetes risk across four distinct machine
                learning paradigms concurrently. Understand the exact physiological factors driving
                every result through mathematically grounded SHAP explanations, missing-data
                sensitivity analysis, and verifiable PDF clinical summaries.
              </p>

              <div className="hero-cta-group">
                <button
                  type="button"
                  className="hero-btn-primary"
                  onClick={() => onNavigate('register')}
                >
                  Start Patient Assessment
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                  >
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
                <button
                  type="button"
                  className="hero-btn-secondary"
                  onClick={() => scrollToSection('pipeline')}
                >
                  Explore How It Works
                </button>
              </div>

              <div className="hero-features-preview">
                <div className="feature-pill">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>4 Independent Models</span>
                </div>
                <div className="feature-pill">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Attributed SHAP Values</span>
                </div>
                <div className="feature-pill">
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Downloadable PDF Reports</span>
                </div>
              </div>
            </div>

            {/* Hero Visual Mockup Component */}
            <div className="hero-visual">
              <div className="mockup-card">
                <div className="mockup-header">
                  <div className="mockup-header-title">
                    <span className="dot-live" />
                    <strong>Interactive Assessment Preview</strong>
                  </div>
                  <div className="mockup-tabs">
                    <button
                      type="button"
                      className={`mockup-tab ${activeTabDemo === 'heart' ? 'active' : ''}`}
                      onClick={() => setActiveTabDemo('heart')}
                    >
                      Heart Disease
                    </button>
                    <button
                      type="button"
                      className={`mockup-tab ${activeTabDemo === 'diabetes' ? 'active' : ''}`}
                      onClick={() => setActiveTabDemo('diabetes')}
                    >
                      Diabetes
                    </button>
                  </div>
                </div>

                <div className="mockup-body">
                  {/* Consensus Meter */}
                  <div className="mockup-consensus-bar">
                    <div className="consensus-info">
                      <span className="consensus-label">Multi-Model Ensemble</span>
                      <span className="consensus-count">4 of 4 Models Agree</span>
                    </div>
                    <div className="models-grid-mini">
                      <div className="model-chip active">Random Forest</div>
                      <div className="model-chip active">Logistic Reg</div>
                      <div className="model-chip active">Gradient Boost</div>
                      <div className="model-chip active">Neural Net (MLP)</div>
                    </div>
                  </div>

                  {/* Prediction Outcome */}
                  <div className="mockup-outcome">
                    <div className="outcome-badge danger">
                      <span className="pulse-danger" />
                      Elevated Risk Detected
                    </div>
                    <div className="outcome-probability">
                      <span className="probability-num">
                        {activeTabDemo === 'heart' ? '78.4%' : '74.2%'}
                      </span>
                      <span className="probability-sub">Uncalibrated Model Score</span>
                    </div>
                  </div>

                  {/* SHAP Factor Bars */}
                  <div className="mockup-factors">
                    <span className="factors-title">
                      Primary Model SHAP Attributions (
                      {activeTabDemo === 'heart' ? 'Random Forest' : 'Logistic Regression'}):
                    </span>
                    {activeTabDemo === 'heart' ? (
                      <>
                        <div className="factor-row">
                          <span className="factor-name">Thallium stress test result (7.0)</span>
                          <span className="factor-val pos">+0.146 (Raises Risk)</span>
                        </div>
                        <div className="factor-bar-wrapper">
                          <div className="factor-bar-fill pos" style={{ width: '85%' }} />
                        </div>

                        <div className="factor-row">
                          <span className="factor-name">Major vessels coloured (2.0)</span>
                          <span className="factor-val pos">+0.077 (Raises Risk)</span>
                        </div>
                        <div className="factor-bar-wrapper">
                          <div className="factor-bar-fill pos" style={{ width: '60%' }} />
                        </div>

                        <div className="factor-row">
                          <span className="factor-name">Resting blood pressure (120 mm Hg)</span>
                          <span className="factor-val neg">-0.024 (Lowers Risk)</span>
                        </div>
                        <div className="factor-bar-wrapper">
                          <div className="factor-bar-fill neg" style={{ width: '30%' }} />
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="factor-row">
                          <span className="factor-name">Plasma glucose (168 mg/dL)</span>
                          <span className="factor-val pos">+0.182 (Raises Risk)</span>
                        </div>
                        <div className="factor-bar-wrapper">
                          <div className="factor-bar-fill pos" style={{ width: '90%' }} />
                        </div>

                        <div className="factor-row">
                          <span className="factor-name">Body mass index (34.2 kg/m²)</span>
                          <span className="factor-val pos">+0.095 (Raises Risk)</span>
                        </div>
                        <div className="factor-bar-wrapper">
                          <div className="factor-bar-fill pos" style={{ width: '65%' }} />
                        </div>

                        <div className="factor-row">
                          <span className="factor-name">Age (25 years)</span>
                          <span className="factor-val neg">-0.038 (Lowers Risk)</span>
                        </div>
                        <div className="factor-bar-wrapper">
                          <div className="factor-bar-fill neg" style={{ width: '38%' }} />
                        </div>
                      </>
                    )}
                  </div>

                  {/* Patient Interpretation Preview */}
                  <div className="mockup-guidance-box">
                    <strong>What This Result Means:</strong>
                    <p>
                      Reflects statistical risk patterns in retrospective research data. Designed to
                      inform collaborative medical consultations, not replace diagnostic testing.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ===== Pipeline Section (How ClariDx Works) ===== */}
        <section id="pipeline" className="pipeline-section">
          <div className="container">
            <div className="section-head text-center">
              <span className="section-subtitle">System Architecture</span>
              <h2 className="section-title">How ClariDx Operates</h2>
              <p className="section-desc">
                From physiological patient inputs to explainable clinical decision-support
                summaries, each assessment undergoes rigorous automated verification.
              </p>
            </div>

            <div className="pipeline-grid">
              <div className="pipeline-step-card">
                <div className="step-number">01</div>
                <div className="step-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                    <polyline points="10 9 9 9 8 9" />
                  </svg>
                </div>
                <h3 className="step-title">Standardized Clinical Inputs</h3>
                <p className="step-text">
                  Enter validated cardiovascular biomarkers (13 features) or metabolic measurements
                  (8 features). Runtime schema validators enforce realistic physiological ranges and
                  prevent unmeasured zeros.
                </p>
              </div>

              <div className="pipeline-step-card">
                <div className="step-number">02</div>
                <div className="step-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
                    <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
                    <line x1="6" y1="6" x2="6.01" y2="6" />
                    <line x1="6" y1="18" x2="6.01" y2="18" />
                  </svg>
                </div>
                <h3 className="step-title">4-Model Concurrent Execution</h3>
                <p className="step-text">
                  All four trained models (Random Forest, Logistic Regression, Gradient Boosting,
                  MLP) execute simultaneously through dedicated, immutable scikit-learn
                  preprocessing pipelines.
                </p>
              </div>

              <div className="pipeline-step-card">
                <div className="step-number">03</div>
                <div className="step-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M12 20v-6M6 20V10M18 20V4" />
                  </svg>
                </div>
                <h3 className="step-title">Deterministic Majority Voting</h3>
                <p className="step-text">
                  Consensus is calculated at a standard 0.50 decision threshold. In the event of a 2
                  vs 2 tie, the primary validated reference model acts as a transparent, documented
                  tie-breaker.
                </p>
              </div>

              <div className="pipeline-step-card">
                <div className="step-number">04</div>
                <div className="step-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                </div>
                <h3 className="step-title">SHAP Attribution &amp; PDF Export</h3>
                <p className="step-text">
                  Mathematical feature attributions explain how the primary model reached its
                  conclusion. Patients can review past assessments or generate official ReportLab
                  PDF clinical summaries.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ===== Supported Conditions Section ===== */}
        <section id="conditions" className="conditions-section">
          <div className="container">
            <div className="section-head text-center">
              <span className="section-subtitle">Evaluated Research Modules</span>
              <h2 className="section-title">Supported Clinical Conditions</h2>
              <p className="section-desc">
                ClariDx implements two distinct, thoroughly tested disease assessment modules based
                on recognized academic research cohorts.
              </p>
            </div>

            <div className="conditions-grid">
              {/* Heart Disease Card */}
              <div className="condition-card">
                <div className="condition-card-header">
                  <div className="condition-icon heart-icon">
                    <svg
                      width="28"
                      height="28"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="condition-title">Heart Disease Risk</h3>
                    <span className="cohort-tag">UCI Cleveland Cohort (303 records)</span>
                  </div>
                </div>

                <p className="condition-description">
                  Predicts the likelihood of ischemic heart disease from physiological and
                  stress-test indicators. Uses 13 clinical biomarkers to model cardiovascular risk.
                </p>

                <div className="condition-specs">
                  <div className="spec-row">
                    <span className="spec-label">Primary Reference Model:</span>
                    <span className="spec-value">Random Forest (Tree Ensemble)</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Clinical Features:</span>
                    <span className="spec-value">
                      13 (Chest Pain, ST Depression, Thallium, BP, etc.)
                    </span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Decision Threshold:</span>
                    <span className="spec-value">0.50 (Uncalibrated raw probability)</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Explainability:</span>
                    <span className="spec-value">TreeSHAP &amp; LIME Local Perturbations</span>
                  </div>
                </div>

                <div className="card-action">
                  <button
                    type="button"
                    className="card-cta-btn"
                    onClick={() => onNavigate('register')}
                  >
                    Evaluate Heart Disease Risk
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Diabetes Card */}
              <div className="condition-card">
                <div className="condition-card-header">
                  <div className="condition-icon diabetes-icon">
                    <svg
                      width="28"
                      height="28"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="condition-title">Diabetes Risk Analysis</h3>
                    <span className="cohort-tag">Pima Indians Cohort (768 records)</span>
                  </div>
                </div>

                <p className="condition-description">
                  Estimates the risk of Type 2 diabetes based on diagnostic metabolic factors.
                  Trained on benchmark retrospective data with zero-as-missing physiological
                  handling.
                </p>

                <div className="condition-specs">
                  <div className="spec-row">
                    <span className="spec-label">Primary Reference Model:</span>
                    <span className="spec-value">Logistic Regression (Glass-Box Reference)</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Metabolic Features:</span>
                    <span className="spec-value">
                      8 (Glucose, Insulin, BMI, Pedigree, BP, etc.)
                    </span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Cohort Demographics:</span>
                    <span className="spec-value">Historical female cohort aged 21+</span>
                  </div>
                  <div className="spec-row">
                    <span className="spec-label">Explainability:</span>
                    <span className="spec-value">LinearSHAP (Log-odds &amp; Probability)</span>
                  </div>
                </div>

                <div className="card-action">
                  <button
                    type="button"
                    className="card-cta-btn"
                    onClick={() => onNavigate('register')}
                  >
                    Evaluate Diabetes Risk
                    <svg
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                    >
                      <line x1="5" y1="12" x2="19" y2="12" />
                      <polyline points="12 5 19 12 12 19" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ===== Explainability (XAI) Section ===== */}
        <section id="explainability" className="xai-section">
          <div className="container">
            <div className="section-head text-center">
              <span className="section-subtitle">Interpretable Healthcare</span>
              <h2 className="section-title">Why Explainability Matters</h2>
              <p className="section-desc">
                In healthcare, black-box predictions are inadequate. A clinician must understand why
                an algorithm arrived at a risk score before discussing it with a patient.
              </p>
            </div>

            <div className="xai-features-grid">
              <div className="xai-card">
                <div className="xai-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                </div>
                <h3>SHAP Feature Attribution</h3>
                <p>
                  Rooted in cooperative game theory (Shapley values), SHAP calculates the exact
                  marginal contribution of each biomarker, showing which measurements increased or
                  decreased risk.
                </p>
              </div>

              <div className="xai-card">
                <div className="xai-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polygon points="12 2 2 7 12 12 22 7 12 2" />
                    <polyline points="2 17 12 22 22 17" />
                    <polyline points="2 12 12 17 22 12" />
                  </svg>
                </div>
                <h3>Single-Model Attribution Honesty</h3>
                <p>
                  SHAP explanations are explicitly attributed to the primary validated model rather
                  than making false claims that a single explanation explains the heuristic 4-model
                  ensemble.
                </p>
              </div>

              <div className="xai-card">
                <div className="xai-icon">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                </div>
                <h3>Missing-Data Sensitivity Analysis</h3>
                <p>
                  When clinical measurements are missing, ClariDx models uncertainty over empirical
                  background distributions rather than presenting misleading, false-precision
                  predictions.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* ===== Clinical Reports & History Section ===== */}
        <section id="reports" className="reports-section">
          <div className="container reports-container">
            <div className="reports-content">
              <span className="section-subtitle">Longitudinal Tracking</span>
              <h2 className="section-title">Auditable Assessment History &amp; PDF Reports</h2>
              <p className="reports-desc">
                Every completed patient assessment is securely persisted in MySQL with strict
                row-level access control. Patients can monitor their health trends over time and
                export comprehensive clinical summaries.
              </p>

              <ul className="reports-checklist">
                <li>
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>
                    <strong>Authoritative UTC Timestamps:</strong> Stored and validated in UTC with
                    dual display showing local browser time and resolved IANA timezone.
                  </span>
                </li>
                <li>
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>
                    <strong>Downloadable Clinical PDF:</strong> Generated server-side using
                    ReportLab with multi-model scores, primary SHAP factors, and clinical safety
                    notices.
                  </span>
                </li>
                <li>
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>
                    <strong>Patient-Friendly Guidance:</strong> Clear &quot;What This Result
                    Means&quot; and &quot;What to Do Next&quot; narrative guidance identical across
                    web and PDF.
                  </span>
                </li>
              </ul>

              <div className="reports-cta">
                <button
                  type="button"
                  className="hero-btn-primary"
                  onClick={() => onNavigate('register')}
                >
                  Create Patient Account
                </button>
              </div>
            </div>

            <div className="reports-preview-box">
              <div className="pdf-preview-card">
                <div className="pdf-header-bar">
                  <div className="pdf-header-left">
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      aria-hidden="true"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                    <span>Clinical Decision Support Summary (PDF)</span>
                  </div>
                  <span className="pdf-sample-badge">Sample Format Preview</span>
                </div>
                <div className="pdf-content-simulation">
                  <div className="pdf-sim-title">ClariDx Decision Support Summary</div>
                  <div className="pdf-sim-meta">
                    <div className="pdf-meta-item">
                      <span className="meta-label">Format Standard:</span>
                      <span className="meta-value">ReportLab Official PDF Export</span>
                    </div>
                    <div className="pdf-meta-item">
                      <span className="meta-label">Included Sections:</span>
                      <span className="meta-value">
                        Consensus Breakdown, Top SHAP Factors, Guidance
                      </span>
                    </div>
                  </div>
                  <div className="pdf-sim-table">
                    <div className="table-row-sim head">
                      <span>Model Architecture</span>
                      <span>Pipeline Verification</span>
                      <span>Consensus Finding</span>
                    </div>
                    <div className="table-row-sim">
                      <span>Random Forest (Ensemble)</span>
                      <span className="status-verified">Verified</span>
                      <span className="status-elevated">Elevated Risk</span>
                    </div>
                    <div className="table-row-sim">
                      <span>Logistic Regression (Glass-Box)</span>
                      <span className="status-verified">Verified</span>
                      <span className="status-elevated">Elevated Risk</span>
                    </div>
                    <div className="table-row-sim">
                      <span>Gradient Boosting (Boosted)</span>
                      <span className="status-verified">Verified</span>
                      <span className="status-elevated">Elevated Risk</span>
                    </div>
                    <div className="table-row-sim">
                      <span>Neural Network (MLP)</span>
                      <span className="status-verified">Verified</span>
                      <span className="status-lower">Lower Risk</span>
                    </div>
                  </div>
                  <div className="pdf-sim-notice">
                    <strong>Sample Clinical Interpretation (Included in PDF):</strong>
                    <p>
                      Share this report with your qualified healthcare provider. Do not alter
                      medications based solely on an automated risk score.
                    </p>
                  </div>
                  <div className="pdf-sim-watermark">
                    SAMPLE PREVIEW ONLY &bull; NOT AN ACTUAL PATIENT RECORD
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ===== Clinical Safety & Limitations Notice ===== */}
        <section id="safety" className="safety-section">
          <div className="container">
            <div className="safety-alert-card">
              <div className="safety-alert-header">
                <div className="safety-icon" aria-hidden="true">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                </div>
                <div>
                  <h3 className="safety-title">
                    Important Academic &amp; Clinical Safety Disclosure
                  </h3>
                  <span className="safety-subtitle">Not a certified medical device</span>
                </div>
              </div>
              <div className="safety-body">
                <p>
                  ClariDx is an educational and academic decision-support prototype. It does not
                  provide medical diagnoses, prognoses, or personalized treatment plans.
                </p>
                <ul className="safety-points">
                  <li>
                    <strong>Raw (Uncalibrated) Scores:</strong> Model probability scores reflect raw
                    algorithm margins and carry{' '}
                    <code style={{ whiteSpace: 'nowrap' }}>calibrated: false</code>.
                  </li>
                  <li>
                    <strong>Historical Datasets:</strong> Models were trained on small,
                    retrospective research cohorts (Cleveland Heart Disease, 303 cases; Pima Indians
                    Diabetes, 768 cases).
                  </li>
                  <li>
                    <strong>Mandatory Clinical Oversight:</strong> Patients must consult
                    board-certified physicians for all diagnostic and therapeutic decisions.
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ===== Global Footer ===== */}
      <footer className="landing-footer">
        <div className="container footer-content">
          <div className="footer-grid">
            <div className="footer-brand-col">
              <div className="brand">
                <div className="brand-mark" aria-hidden="true">
                  Cx
                </div>
                <div className="brand-text">
                  <span className="brand-name">ClariDx</span>
                  <span className="brand-tagline">Clinical AI you can see through</span>
                </div>
              </div>
              <p className="footer-mission">
                Transparent machine learning decision support engineered for educational
                transparency and clinical review.
              </p>
            </div>

            <div className="footer-links-col">
              <h4>System Modules</h4>
              <ul>
                <li>
                  <button type="button" onClick={() => scrollToSection('conditions')}>
                    Heart Disease Assessment
                  </button>
                </li>
                <li>
                  <button type="button" onClick={() => scrollToSection('conditions')}>
                    Diabetes Risk Analysis
                  </button>
                </li>
                <li>
                  <button type="button" onClick={() => scrollToSection('pipeline')}>
                    Multi-Model Consensus
                  </button>
                </li>
                <li>
                  <button type="button" onClick={() => scrollToSection('explainability')}>
                    SHAP &amp; LIME Attribution
                  </button>
                </li>
              </ul>
            </div>

            <div className="footer-links-col">
              <h4>User Access</h4>
              <ul>
                <li>
                  <button type="button" onClick={() => onNavigate('login')}>
                    Sign In to Portal
                  </button>
                </li>
                <li>
                  <button type="button" onClick={() => onNavigate('register')}>
                    Patient Registration
                  </button>
                </li>
                <li>
                  <button type="button" onClick={() => onNavigate('request-access')}>
                    Clinical Access Guidance
                  </button>
                </li>
                <li>
                  <button type="button" onClick={() => scrollToSection('reports')}>
                    Downloadable Reports
                  </button>
                </li>
              </ul>
            </div>

            <div className="footer-links-col">
              <h4>Academic References</h4>
              <ul>
                <li>
                  <span>UCI Heart Disease (1988)</span>
                </li>
                <li>
                  <span>Pima Indians Diabetes (OpenML 37)</span>
                </li>
                <li>
                  <span>SHAP: Lundberg &amp; Lee (NeurIPS 2017)</span>
                </li>
                <li>
                  <span>LIME: Ribeiro et al. (KDD 2016)</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="footer-bottom">
            <p className="footer-copy">
              &copy; {new Date().getFullYear()} ClariDx. Academic Clinical Decision Support
              Prototype. Licensed under MIT.
            </p>
            <p className="footer-disclaimer">
              Not evaluated by the FDA or CE for autonomous medical diagnosis.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
