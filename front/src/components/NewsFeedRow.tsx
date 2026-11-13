import type { NewsFeed } from '../api'
import { formatRelativeDate } from '../format'

type Props = {
  feed: NewsFeed
}

/** One RSS source as a full-width band: its name/logo on the left, its articles in a row. */
export function NewsFeedRow({ feed }: Props) {
  return (
    <div className="news-row">
      <a className="news-row-head" href={feed.site_url} target="_blank" rel="noreferrer">
        <img src={feed.logo_url} alt="" width={20} height={20} />
        <span>{feed.name}</span>
      </a>

      {feed.error && <p className="error news-row-error">{feed.error}</p>}
      {!feed.error && feed.articles.length === 0 && (
        <p className="muted news-row-error">Aucun article pour l'instant.</p>
      )}

      {feed.articles.length > 0 && (
        <div className="news-row-articles">
          {feed.articles.map((article) => (
            <a
              key={article.url}
              className="news-article"
              href={article.url}
              target="_blank"
              rel="noreferrer"
            >
              <img src={article.image_url ?? feed.logo_url} alt="" loading="lazy" />
              <span className="news-article-title">{article.title}</span>
              {article.published_at && (
                <span className="muted news-article-date">
                  {formatRelativeDate(article.published_at)}
                </span>
              )}
            </a>
          ))}
        </div>
      )}
    </div>
  )
}
