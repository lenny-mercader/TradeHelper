import { useEffect, useState } from 'react'

type HelloResponse = {
  message: string
}

function App() {
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/hello')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json() as Promise<HelloResponse>
      })
      .then((data) => setMessage(data.message))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
  }, [])

  if (error) return <h1>Erreur : {error}</h1>
  if (message === null) return <h1>Chargement…</h1>
  return <h1>{message}</h1>
}

export default App
