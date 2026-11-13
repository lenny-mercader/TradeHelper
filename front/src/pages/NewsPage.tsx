import { NewsSection } from '../components/NewsSection'

export function NewsPage() {
  return (
    <>
      <h1>Actualité</h1>
      <p className="muted">Les 15 derniers articles de chaque source.</p>
      <NewsSection limit={15} title="" />
    </>
  )
}
