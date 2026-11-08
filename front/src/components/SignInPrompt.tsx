import { SignInButton } from '@clerk/react'

/** Shown instead of the watchlist to anonymous visitors. */
export function SignInPrompt() {
  return (
    <div className="panel signin-prompt">
      <p>Connectez-vous pour accéder à la liste de suivi.</p>
      <SignInButton mode="modal">
        <button type="button">Se connecter</button>
      </SignInButton>
    </div>
  )
}
