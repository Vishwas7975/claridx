import { useAuth } from '../auth/AuthContext'
import { useState } from 'react'
import { ApiError } from '../../api/errors'
import type { ModelName } from '../../api/types'
import { ErrorNotice } from '../../components/ErrorNotice'
import { buildPatient, toFormValues, type FormValues } from './form'
import { useFeatures, usePrediction } from './hooks'
import { PatientForm } from './PatientForm'
import { ResultView } from './ResultView'

export function PredictionPage() {
  const { user } = useAuth()
  const isResearcher = user?.role?.toLowerCase() === 'researcher'
  const features = useFeatures()
  const prediction = usePrediction()
  const [values, setValues] = useState<FormValues>({})
  const [modelName, setModelName] = useState<ModelName>('random_forest')

  if (features.isPending) return <p role="status">Loading the measurement form&hellip;</p>
  if (features.isError) {
    return (
      <ErrorNotice
        title="Cannot load the form"
        error={features.error}
        onRetry={() => void features.refetch()}
      />
    )
  }

  const specs = features.data
  const serverIssues = prediction.error instanceof ApiError ? prediction.error.issues : []

  // Any edit invalidates the shown result, so a result always matches the form.
  function edit(update: () => void) {
    prediction.reset()
    update()
  }

  return (
    <div className="layout">
      <PatientForm
        specs={specs}
        values={values}
        onChange={(name, value) =>
          edit(() => setValues((current) => ({ ...current, [name]: value })))
        }
        onApplyExample={(patient) => edit(() => setValues(toFormValues(patient)))}
        onClear={() => edit(() => setValues({}))}
        modelName={modelName}
        onModelChange={(name) => edit(() => setModelName(name))}
        serverIssues={serverIssues}
        submitting={prediction.isPending}
        onSubmit={() => prediction.mutate({ patient: buildPatient(specs, values), modelName })}
        canPredict={!isResearcher}
      />
      <div className="results">
        {prediction.isPending && <p role="status">Analysing&hellip;</p>}
        {prediction.isError && <ErrorNotice title="Analysis failed" error={prediction.error} />}
        {prediction.isSuccess && <ResultView result={prediction.data} />}
        {prediction.isIdle && (
          <p className="placeholder">The result will appear here after you analyse a patient.</p>
        )}
      </div>
    </div>
  )
}
