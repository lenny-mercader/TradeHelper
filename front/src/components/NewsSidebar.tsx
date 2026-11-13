import { useEffect, useState } from 'react'
import { api, type NewsFeed } from '../api'
import { formatRelativeDate } from '../format'
import { useApi } from '../hooks/useApi'
import { Status } from './Status'

const ARTICLES_PER_FEED = 5
const AUTO_ADVANCE_MS = 60_000

type Props = {
  onClose: () => void
}

function FeedCarousel({ feed }: { feed: NewsFeed }) {
  const [index, setIndex] = useState(0)
  const count = feed.articles.length
  const article = count > 0 ? feed.articles[index % count] : null
  const move = (delta: number) => setIndex((i) => (i + delta + count) % count)

  // Loops on its own every minute; a manual click above resets the clock (the effect re-runs
  // because `index` is a dependency), so it doesn't also jump right after someone navigates.
  useEffect(() => {
    if (count <= 1) return
    const id = setInterval(() => move(1), AUTO_ADVANCE_MS)
    return () => clearInterval(id)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [count, index])

  return (
    <div className="news-sidebar-feed">
      <a className="news-row-head" href={feed.site_url} target="_blank" rel="noreferrer">
        <img src={feed.logo_url} alt="" width={18} height={18} />
        <span>{feed.name}</span>
      </a>

      {feed.error && <p className="error news-row-error">{feed.error}</p>}

      {article && (
        <div className="news-carousel">
          <a className="news-carousel-article" href={article.url} target="_blank" rel="noreferrer">
            <img src={article.image_url ?? feed.logo_url} alt="" loading="lazy" />
            <span className="news-sidebar-title">{article.title}</span>
            {article.published_at && (
              <span className="muted news-sidebar-date">
                {formatRelativeDate(article.published_at)}
              </span>
            )}
          </a>
          {count > 1 && (
            <div className="news-carousel-nav">
              <button
                type="button"
                className="link"
                aria-label="Article précédent"
                onClick={() => move(-1)}
              >
                ‹
              </button>
              <span className="muted">
                {(index % count) + 1}/{count}
              </span>
              <button
                type="button"
                className="link"
                aria-label="Article suivant"
                onClick={() => move(1)}
              >
                ›
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

/** Narrow left column: the 5 RSS sources, one article at a time per feed, cycled with ‹ ›. */
export function NewsSidebar({ onClose }: Props) {
  const news = useApi(`news:${ARTICLES_PER_FEED}`, () => api.news(ARTICLES_PER_FEED))

  return (
    <aside className="news-sidebar">
      <div className="news-sidebar-head">
        <h2>Actualité</h2>
        <button type="button" className="link" onClick={onClose}>
          Masquer
        </button>
      </div>
      <Status loading={news.loading} error={news.error} />
      {news.data?.map((feed) => <FeedCarousel key={feed.id} feed={feed} />)}
    </aside>
  )
}
