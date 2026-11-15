import { useState } from 'react'
import { api, type InstrumentProfile } from '../api'
import {
  formatCompactLocal,
  formatFractionPercent,
  formatLocal,
  formatRatio,
  formatVolume,
} from '../format'
import { useApi } from '../hooks/useApi'
import { Status } from './Status'

const TABS = ['Profil', 'Valorisation', 'Analystes', 'Dividende', 'Marché'] as const
type Tab = (typeof TABS)[number]

const DASH = '—'

const RECOMMENDATION_LABELS: Record<string, string> = {
  strong_buy: 'Achat fort',
  buy: 'Achat',
  hold: 'Conserver',
  underperform: 'Sous-performance',
  sell: 'Vente',
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="profile-field">
      <span className="muted">{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function ProfilTab({ p }: { p: InstrumentProfile }) {
  return (
    <>
      {p.summary && <p className="profile-summary">{p.summary}</p>}
      <div className="profile-grid">
        <Field label="Secteur" value={p.sector ?? DASH} />
        <Field label="Industrie" value={p.industry ?? DASH} />
        <Field label="Pays" value={p.country ?? DASH} />
        <Field label="Employés" value={p.employees != null ? formatVolume(p.employees) : DASH} />
        {p.website && (
          <div className="profile-field">
            <span className="muted">Site web</span>
            <a href={p.website} target="_blank" rel="noreferrer">
              {p.website.replace(/^https?:\/\//, '')}
            </a>
          </div>
        )}
      </div>
    </>
  )
}

function ValorisationTab({ p, currency }: { p: InstrumentProfile; currency: string | null }) {
  return (
    <div className="profile-grid">
      <Field label="Capitalisation" value={formatCompactLocal(p.market_cap, currency)} />
      <Field label="Valeur d'entreprise" value={formatCompactLocal(p.enterprise_value, currency)} />
      <Field label="PER" value={p.trailing_pe != null ? p.trailing_pe.toFixed(1) : DASH} />
      <Field label="PER prévisionnel" value={p.forward_pe != null ? p.forward_pe.toFixed(1) : DASH} />
      <Field label="Prix / valeur comptable" value={p.price_to_book != null ? p.price_to_book.toFixed(2) : DASH} />
      <Field label="Bénéfice par action" value={formatLocal(p.eps, currency)} />
      <Field label="Marge bénéficiaire" value={formatFractionPercent(p.profit_margin)} />
      <Field label="Rentabilité des capitaux (ROE)" value={formatFractionPercent(p.return_on_equity)} />
      <Field label="Dette / fonds propres" value={formatRatio(p.debt_to_equity)} />
    </div>
  )
}

function AnalystesTab({ p, currency }: { p: InstrumentProfile; currency: string | null }) {
  if (p.analyst_count == null) {
    return <p className="muted">Aucun avis d'analyste disponible pour cette action.</p>
  }
  return (
    <div className="profile-grid">
      <Field
        label="Recommandation"
        value={p.recommendation ? (RECOMMENDATION_LABELS[p.recommendation] ?? p.recommendation) : DASH}
      />
      <Field label="Objectif de cours moyen" value={formatLocal(p.target_mean_price, currency)} />
      <Field label="Nombre d'analystes" value={String(p.analyst_count)} />
    </div>
  )
}

function DividendeTab({ p, currency }: { p: InstrumentProfile; currency: string | null }) {
  return (
    <div className="profile-grid">
      <Field label="Rendement du dividende" value={formatRatio(p.dividend_yield)} />
      <Field label="Plus haut (52 sem.)" value={formatLocal(p.week52_high, currency)} />
      <Field label="Plus bas (52 sem.)" value={formatLocal(p.week52_low, currency)} />
      <Field label="Volume moyen" value={formatVolume(p.average_volume)} />
    </div>
  )
}

function MarcheTab({ p }: { p: InstrumentProfile }) {
  return (
    <div className="profile-grid">
      <Field
        label="Transactions aujourd'hui"
        value={p.is_us ? (p.transactions_today != null ? formatVolume(p.transactions_today) : DASH) : 'Non disponible'}
      />
      <Field label="VIX (volatilité du marché US)" value={p.vix ? p.vix.value.toFixed(1) : DASH} />
      {p.vix && <Field label="Niveau" value={p.vix.label} />}
    </div>
  )
}

type Props = {
  symbol: string
  currency: string | null
}

export function ProfileTabs({ symbol, currency }: Props) {
  const [tab, setTab] = useState<Tab>('Profil')
  const profile = useApi(symbol, () => api.profile(symbol))

  return (
    <section className="panel profile-tabs">
      <div className="segmented" role="tablist" aria-label="Informations complémentaires">
        {TABS.map((t) => (
          <button key={t} type="button" role="tab" aria-selected={tab === t} aria-pressed={tab === t} onClick={() => setTab(t)}>
            {t}
          </button>
        ))}
      </div>

      <Status loading={profile.loading} error={profile.error} />
      {profile.data && (
        <div className="profile-content" role="tabpanel">
          {tab === 'Profil' && <ProfilTab p={profile.data} />}
          {tab === 'Valorisation' && <ValorisationTab p={profile.data} currency={currency} />}
          {tab === 'Analystes' && <AnalystesTab p={profile.data} currency={currency} />}
          {tab === 'Dividende' && <DividendeTab p={profile.data} currency={currency} />}
          {tab === 'Marché' && <MarcheTab p={profile.data} />}
        </div>
      )}
      {profile.data && (
        <p className="muted profile-footnote">
          Données Yahoo Finance{profile.data.vix ? ' et CBOE (VIX)' : ''}, informatives, non mises
          à jour en continu.
        </p>
      )}
    </section>
  )
}
