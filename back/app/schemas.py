"""API models. Every amount named `close`/`high_52w`... is in EUR; `*_local` is in `currency`."""

import datetime as dt

from pydantic import BaseModel


class Quote(BaseModel):
    symbol: str
    name: str | None
    exchange: str | None
    currency: str | None
    date: dt.date | None
    close: float | None
    close_local: float | None
    change_percent: float | None
    volume: int | None
    followed: bool
    # Always false when not followed (favoriting requires being in the watchlist).
    favorite: bool = False


class HistoryPoint(BaseModel):
    date: dt.date
    close: float | None
    close_local: float
    volume: int


class SearchResult(BaseModel):
    symbol: str
    name: str | None
    exchange: str | None
    type: str | None


class Mover(BaseModel):
    symbol: str
    name: str | None
    date: dt.date
    close: float | None
    close_local: float
    currency: str
    change_percent: float
    volume: int


class Movers(BaseModel):
    date: dt.date | None
    gainers: list[Mover]
    losers: list[Mover]


class HeatmapTile(BaseModel):
    symbol: str
    name: str | None
    close: float | None
    close_local: float
    currency: str
    change_percent: float
    volume: int
    # Dollar volume (close * volume): a free proxy for company size, used to size each tile
    # (we have no market cap data source). Not displayed as such in the UI.
    dollar_volume: float


class Heatmap(BaseModel):
    date: dt.date | None
    tiles: list[HeatmapTile]


class CompareRow(BaseModel):
    symbol: str
    name: str | None = None
    currency: str | None = None
    close: float | None = None
    perf_1m: float | None = None
    perf_1y: float | None = None
    perf_5y: float | None = None
    volatility_1y: float | None = None
    high_52w: float | None = None
    low_52w: float | None = None
    error: str | None = None


class PerformanceSeries(BaseModel):
    symbol: str
    name: str | None
    currency: str | None
    # Change in % (EUR) since the period start, aligned on PerformanceOut.dates.
    # None before the instrument's first known day.
    values: list[float | None]


class PerformanceOut(BaseModel):
    period: str
    start: dt.date | None
    end: dt.date | None
    dates: list[dt.date]
    series: list[PerformanceSeries]
    # Symbols that could not be computed, with the reason (displayed as-is).
    errors: dict[str, str]


class NewsArticle(BaseModel):
    title: str
    url: str
    published_at: dt.datetime | None
    # None when the feed gives no image for this article; the front falls back to the source logo.
    image_url: str | None


class NewsFeed(BaseModel):
    id: str
    name: str
    site_url: str
    # Small icon of the source (Google's favicon service), also the fallback for articles with
    # no image.
    logo_url: str
    articles: list[NewsArticle]
    # Set when this feed could not be fetched/parsed; `articles` is then empty (others still show).
    error: str | None = None


class CatalogRow(BaseModel):
    symbol: str
    name: str | None
    country: str | None
    sector: str | None
    currency: str | None
    close: float | None  # EUR
    change_percent: float | None
    # EUR, like `close` — "—" until the instrument's profile is loaded.
    market_cap: float | None


class CatalogPage(BaseModel):
    rows: list[CatalogRow]
    total: int
    page: int
    page_size: int


class CatalogFacets(BaseModel):
    countries: list[str]
    sectors: list[str]


class Vix(BaseModel):
    value: float
    label: str


class InstrumentProfile(BaseModel):
    """Everything for the stock page's tabs beyond the quote itself. All fields optional: not
    every instrument has every field (ETFs have no sector; some tickers lack analyst coverage)."""

    is_us: bool

    # Profile
    sector: str | None = None
    industry: str | None = None
    summary: str | None = None
    country: str | None = None
    website: str | None = None
    employees: int | None = None

    # Valorisation & rentabilité
    market_cap: float | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    enterprise_value: float | None = None
    price_to_book: float | None = None
    profit_margin: float | None = None
    return_on_equity: float | None = None
    debt_to_equity: float | None = None
    eps: float | None = None

    # Analystes
    recommendation: str | None = None
    target_mean_price: float | None = None
    analyst_count: int | None = None

    # Dividende & range 52 semaines
    dividend_yield: float | None = None
    week52_high: float | None = None
    week52_low: float | None = None
    average_volume: int | None = None

    # Marché
    transactions_today: int | None = None  # US only (Massive); null otherwise
    vix: Vix | None = None
