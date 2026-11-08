# TradeHelper

- `front/` : React + TypeScript (Vite, npm, React Router, Recharts), déployé sur Vercel
- `back/` : Python 3.15 + FastAPI (Poetry, SQLAlchemy 2, Alembic), déployé sur Render
- Base : Postgres (conteneur en local, Neon en production)

## Données

Modèle « à la demande » : on ne stocke pas tout le marché mondial.

| Source | Usage |
| --- | --- |
| **Massive** (ex-Polygon, gratuit : 5 appels/min) | Catalogue des ~11 000 actions/ETF US (recherche), clôture de **tout** le marché US en 1 appel par soir (top hausses/baisses), splits, secours historique US (2 ans) |
| **Yahoo Finance** (yfinance, non officiel) | Toutes les bourses mondiales : recherche, historique 5 ans chargé à la 1re ouverture d'une action |
| **BCE** (API Frankfurter, sans clé) | Taux de change EUR quotidiens (~30 devises) ; Yahoo pour les autres |

- Les prix sont stockés **dans la devise locale** (pence/cents convertis en GBP/ZAR/ILS) et
  **ajustés des splits** (pas des dividendes). Un split déclenche le rechargement de l'historique.
- L'API renvoie tout **en EUR** (taux du jour de chaque séance) ; `close_local` garde le prix d'origine.
- Une action ouverte est mise à jour au plus une fois par jour ; les actions **suivies** le sont
  chaque soir par le job planifié.

## Lancer en local

1. Copier `back/.env.example` en `back/.env` et remplir `MASSIVE_API_KEY` et `REFRESH_TOKEN`
   (`DATABASE_URL` est fourni par docker-compose). Ne jamais commiter `.env`.
2. Démarrer :

   ```bash
   docker compose up --build
   ```

3. Base locale vide : charger le catalogue US (~2 min) puis la clôture du marché :

   ```bash
   curl -X POST -H "Authorization: Bearer <REFRESH_TOKEN>" http://localhost:8000/api/catalog/refresh
   curl -X POST -H "Authorization: Bearer <REFRESH_TOKEN>" http://localhost:8000/api/refresh
   ```

- Front : http://localhost:5173
- API : http://localhost:8000 (Swagger : http://localhost:8000/docs)

## API

| Méthode | Route | Rôle |
| --- | --- | --- |
| GET | `/api/search?q=` | Catalogue local (US + actions déjà ouvertes), complété par Yahoo |
| GET | `/api/instruments/{symbol}` | Dernière clôture (EUR + locale) ; charge l'historique à la 1re ouverture |
| GET | `/api/instruments/{symbol}/history` | Historique quotidien en EUR |
| GET | `/api/watchlist` | Actions suivies |
| POST / DELETE | `/api/watchlist/{symbol}` | Suivre / ne plus suivre |
| GET | `/api/market/movers` | Plus fortes hausses/baisses US de la dernière séance |
| GET | `/api/compare?symbols=A,B` | Perf 1 mois / 1 an / 5 ans, volatilité, plus haut/bas 52 sem. (EUR, 10 max) |
| POST | `/api/refresh` | Job du soir (token Bearer) : marché US, actions suivies, taux de change |
| POST | `/api/catalog/refresh` | Job hebdo (token Bearer) : catalogue US |

## Production

- **Vercel** (root `front`) : `front/vercel.json` redirige `/api/*` vers Render et sert
  `index.html` pour les routes du front.
- **Render** (root `back`) : variables `DATABASE_URL` (URL Neon), `MASSIVE_API_KEY`, `REFRESH_TOKEN`.
- **GitHub Actions** (secret `REFRESH_TOKEN`, même valeur que sur Render) :
  - `daily-refresh.yml` : `POST /api/refresh` à 22:30 UTC du lundi au vendredi ;
  - `weekly-catalog.yml` : `POST /api/catalog/refresh` le dimanche à 06:00 UTC.
  Les deux se lancent aussi à la main (onglet Actions, « Run workflow »).
- Limite connue : Yahoo bloque parfois les IP de serveurs cloud. Dans ce cas les actions US
  restent servies par Massive (2 ans d'historique), les actions internationales non.
