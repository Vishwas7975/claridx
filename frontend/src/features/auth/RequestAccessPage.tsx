interface Props {
  onBack: () => void
}

export function RequestAccessPage({ onBack }: Props) {
  return (
    <div className="request-access-page">
      <div className="request-access-card">
        <div className="request-access-icon" aria-hidden="true">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--accent)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <rect width="18" height="11" x="3" y="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
        </div>

        <h2>Request a ClariDx Account</h2>

        <p className="request-access-intro">
          ClariDx uses administrator-provisioned accounts to maintain clinical governance and
          role-based access control. Accounts are not self-registered.
        </p>

        <div className="request-access-steps">
          <div className="request-step">
            <div className="step-num">1</div>
            <p className="step-text">
              Contact your institution&rsquo;s ClariDx administrator or research coordinator.
            </p>
          </div>
          <div className="request-step">
            <div className="step-num">2</div>
            <p className="step-text">
              Provide your full name, institutional email address, and the role you require —{' '}
              <strong>Doctor</strong> (prediction access) or <strong>Researcher</strong> (read-only
              model inspection).
            </p>
          </div>
          <div className="request-step">
            <div className="step-num">3</div>
            <p className="step-text">
              The administrator will provision your account using the secure ClariDx CLI and notify
              you when access is ready.
            </p>
          </div>
        </div>

        <div className="request-access-note">
          <strong>Why administrator provisioning?</strong> ClariDx handles clinical decision support
          outputs. Role assignment is verified by a responsible administrator to ensure that
          prediction access is granted only to authorised clinical personnel.
        </div>

        <a
          href="#login"
          className="ra-back-link"
          onClick={(e) => {
            e.preventDefault()
            onBack()
          }}
        >
          ← Back to Sign in
        </a>
      </div>
    </div>
  )
}
