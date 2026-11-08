type Props = {
  loading?: boolean
  error?: string
  loadingText?: string
}

/** Loading / error line shared by every page. Renders nothing once data is there. */
export function Status({ loading, error, loadingText = 'Chargement…' }: Props) {
  if (error) return <p className="error">Erreur : {error}</p>
  if (loading) return <p className="muted">{loadingText}</p>
  return null
}
