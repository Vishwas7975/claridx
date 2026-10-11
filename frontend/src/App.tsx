import { PredictionPage } from './features/heart/PredictionPage'

export default function App() {
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
        <PredictionPage />
      </main>
    </>
  )
}
