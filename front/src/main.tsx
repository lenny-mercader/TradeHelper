import { frFR } from '@clerk/localizations'
import { ClerkProvider } from '@clerk/react'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router'
import './index.css'
import App from './App.tsx'

// Public by design (it identifies the Clerk application, it grants nothing).
const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined

const root = createRoot(document.getElementById('root')!)

if (!publishableKey) {
  root.render(
    <p style={{ padding: 16 }}>
      Configuration manquante : VITE_CLERK_PUBLISHABLE_KEY (front/.env.local en local, variable
      d'environnement sur Vercel).
    </p>,
  )
} else {
  root.render(
    <StrictMode>
      <ClerkProvider publishableKey={publishableKey} localization={frFR}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ClerkProvider>
    </StrictMode>,
  )
}
