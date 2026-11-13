import { api } from '../api'
import { useApi } from '../hooks/useApi'
import { NewsFeedRow } from './NewsFeedRow'
import { Status } from './Status'

type Props = {
  /** 5 on the homepage, 15 on the Actualité page. */
  limit: number
  title?: string
}

/** The 5 fixed RSS sources, one full-width band per source. Public: no sign-in needed. */
export function NewsSection({ limit, title = 'Actualités' }: Props) {
  const news = useApi(`news:${limit}`, () => api.news(limit))

  return (
    <section className="news-section">
      {title && <h2>{title}</h2>}
      <Status loading={news.loading} error={news.error} />
      {news.data?.map((feed) => <NewsFeedRow key={feed.id} feed={feed} />)}
    </section>
  )
}
