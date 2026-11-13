import { api } from '../api'
import { formatRelativeDate } from '../format'
import { useApi } from '../hooks/useApi'
import { Status } from './Status'

const ARTICLES_PER_FEED = 5

type Props = {
  onClose: () => void
}

/** Narrow left column: the 5 RSS sources, 5 latest articles each, collapsible (hides entirely). */
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
      {news.data?.map((feed) => (
        <div key={feed.id} className="news-sidebar-feed">
          <a className="news-row-head" href={feed.site_url} target="_blank" rel="noreferrer">
            <img src={feed.logo_url} alt="" width={18} height={18} />
            <span>{feed.name}</span>
          </a>
          {feed.error && <p className="error news-row-error">{feed.error}</p>}
          <ul className="news-sidebar-list">
            {feed.articles.map((article) => (
              <li key={article.url}>
                <a href={article.url} target="_blank" rel="noreferrer">
                  <img src={article.image_url ?? feed.logo_url} alt="" loading="lazy" />
                  <span className="news-sidebar-text">
                    <span className="news-sidebar-title">{article.title}</span>
                    {article.published_at && (
                      <span className="muted news-sidebar-date">
                        {formatRelativeDate(article.published_at)}
                      </span>
                    )}
                  </span>
                </a>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </aside>
  )
}
