import { Show, SignInButton, SignUpButton, UserButton } from '@clerk/react'
import { Link, NavLink, Route, Routes, useNavigate } from 'react-router'
import { SearchBox } from './components/SearchBox'
import { ComparePage } from './pages/ComparePage'
import { MarketPage } from './pages/MarketPage'
import { StockPage } from './pages/StockPage'
import { WatchlistPage } from './pages/WatchlistPage'

function App() {
  const navigate = useNavigate()

  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">
          TradeHelper
        </Link>
        <nav>
          <NavLink to="/" end>
            Marché
          </NavLink>
          <NavLink to="/watchlist">Suivies</NavLink>
          <NavLink to="/compare">Comparer</NavLink>
        </nav>
        <SearchBox onSelect={(r) => navigate(`/stock/${encodeURIComponent(r.symbol)}`)} />
        <div className="account">
          <Show when="signed-out">
            <SignInButton mode="modal">
              <button type="button" className="secondary">
                Se connecter
              </button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button type="button">S'inscrire</button>
            </SignUpButton>
          </Show>
          <Show when="signed-in">
            <UserButton />
          </Show>
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<MarketPage />} />
          <Route path="/watchlist" element={<WatchlistPage />} />
          <Route path="/stock/:symbol" element={<StockPage />} />
          <Route path="/compare" element={<ComparePage />} />
          <Route
            path="*"
            element={
              <p>
                Page introuvable. <Link to="/">Retour au marché</Link>
              </p>
            }
          />
        </Routes>
      </main>
    </>
  )
}

export default App
