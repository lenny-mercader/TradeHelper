# TradeHelper

- `front/` : React + TypeScript (Vite, npm, Recharts), déployé sur Vercel
- `back/` : Python 3.15 + FastAPI (Poetry, SQLAlchemy 2, Alembic), déployé sur Render
- Base : Postgres (conteneur en local, Neon en production)
- Données : Alpha Vantage `TIME_SERIES_DAILY` pour SPY, QQQ, DIA, IWM, VTI, mises à jour chaque soir de semaine

## Lancer en local

1. Copier `back/.env.example` en `back/.env` et remplir `ALPHA_VANTAGE_API_KEY` et `REFRESH_TOKEN`
   (`DATABASE_URL` est fourni par docker-compose). Ne jamais commiter `.env`.
2. Démarrer :

   ```bash
   docker compose up --build
   ```

- Front : http://localhost:5173
- API : http://localhost:8000 (Swagger : http://localhost:8000/docs)

Les migrations Alembic s'appliquent au démarrage du back. La base locale est vide au départ :
lancer une mise à jour à la main (consomme 1 requête Alpha Vantage par symbole, 25/jour en gratuit) :

```bash
curl -X POST -H "Authorization: Bearer <REFRESH_TOKEN>" http://localhost:8000/api/refresh
```

## API

| Méthode | Route | Rôle |
| --- | --- | --- |
| GET | `/api/quotes` | Dernière clôture de chaque symbole + variation vs la veille |
| GET | `/api/quotes/{symbol}/history` | Historique daily (~100 séances) |
| POST | `/api/refresh` | Récupère les données Alpha Vantage (token Bearer requis) |

## Production

- **Vercel** (root `front`) : `front/vercel.json` redirige `/api/*` vers Render.
- **Render** (root `back`) : variables d'environnement `DATABASE_URL` (URL Neon),
  `ALPHA_VANTAGE_API_KEY`, `REFRESH_TOKEN`.
- **GitHub Actions** : `.github/workflows/daily-refresh.yml` appelle `POST /api/refresh` à 22:30 UTC
  du lundi au vendredi. Secret de dépôt requis : `REFRESH_TOKEN` (même valeur que sur Render).
  Lancement manuel possible depuis l'onglet Actions (« Run workflow »).
