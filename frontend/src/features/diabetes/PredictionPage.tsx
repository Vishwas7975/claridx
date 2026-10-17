import { useAuth } from '../auth/AuthContext'
import { useState } from 'react'
import { ApiError } from '../../api/errors'
import type { DiabetesModelName } from '../../api/types'
import { ErrorNotice } from '../../components/ErrorNotice'
import { ResultsEmptyState } from '../../components/ResultsEmptyState'
import { buildPatient, MIN_MEASUREMENTS, toFormValues, type FormValues } from './form'
import { useFeatures, useModels, usePrediction } from './hooks'
import { PatientForm } from './PatientForm'
import { ResultView } from './ResultView'

export function PredictionPage() {
  const { user } = useAuth()
  const isResearcher = user?.role?.toLowerCase() === 'researcher'
  const features = useFeatures()
  const models = useModels()
  const prediction = usePrediction()
  const [values, setValues] = useState<FormValues>({})
  const [modelName, setModelName] = useState<DiabetesModelName>('logistic_regression')

  if (features.isPending || models.isPending) {
    return <p role="status">Loading the measurement form&hellip;</p>
  }

  if (features.isError) {
    return (
      <ErrorNotice
        title="Cannot load the form"
        error={features.error}
        onRetry={() => {
          void features.refetch()
          void models.refetch()
        }}
      />
    )
  }

  if (models.isError) {
    return (
      <ErrorNotice
        title="Cannot load the form"
        error={models.error}
        onRetry={() => {
          void features.refetch()
          void models.refetch()
        }}
      />
    )
  }

  const specs = features.data
  const availableModels = models.data.models
  const serverIssues = prediction.error instanceof ApiError ? prediction.error.issues : []

  function edit(update: () => void) {
    prediction.reset()
    update()
  }

  return (
    <div className="layout">
      <PatientForm
        specs={specs}
        models={availableModels}
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
        {prediction.isSuccess && <ResultView result={prediction.data} specs={specs} />}
        {prediction.isIdle && (
          <ResultsEmptyState
            condition="diabetes"
            modelName={modelName}
            minMeasurements={MIN_MEASUREMENTS}
            totalMeasurements={specs.length}
          />
        )}
      </div>
    </div>
  )
}
