import { useState } from 'react'
import { PredictionPage as DiabetesPredictionPage } from './features/diabetes/PredictionPage'
import { PredictionPage as HeartPredictionPage } from './features/heart/PredictionPage'

export type Condition = 'heart' | 'diabetes'

export default function App() {
  const [condition, setCondition] = useState<Condition>('heart')

  return (
    <>
      <header className="app-header">
        <div className="container">
          <h1>ClariDx</h1>
          <p>Clinical AI you can see through</p>
        </div>
      </header>
      <main className="container">
        <p className="banner" role="note">
          Research prototype for decision support and education only. It is not a medical device and
          must not be used for diagnosis or treatment.
        </p>

        <nav className="condition-nav" aria-label="Condition selector">
          <div className="condition-selector" role="group" aria-label="Conditions">
            <button
              type="button"
              className={condition === 'heart' ? 'condition-btn active' : 'condition-btn secondary'}
              aria-pressed={condition === 'heart'}
              onClick={() => setCondition('heart')}
            >
              Heart Disease
            </button>
            <button
              type="button"
              className={
                condition === 'diabetes' ? 'condition-btn active' : 'condition-btn secondary'
              }
              aria-pressed={condition === 'diabetes'}
              onClick={() => setCondition('diabetes')}
            >
              Diabetes
            </button>
          </div>
        </nav>

        {condition === 'heart' ? (
          <HeartPredictionPage key="heart" />
        ) : (
          <DiabetesPredictionPage key="diabetes" />
        )}
      </main>
    </>
  )
}
