# TradeHelper

- `front/` : React + TypeScript (Vite, npm, Recharts), déployé sur Vercel
- `back/` : Python 3.15 + FastAPI (Poetry, SQLAlchemy 2, Alembic), déployé sur Render
- Base : Postgres (conteneur en local, Neon en production)
- Données : Tiingo EOD (prix bruts, non ajustés) pour 5 ETF + 35 grandes capitalisations US
  (liste dans `back/app/config.py`), 5 ans d'historique, mises à jour chaque soir de semaine

## Lancer en local

1. Copier `back/.env.example` en `back/.env` et remplir `TIINGO_API_KEY` et `REFRESH_TOKEN`
   (`DATABASE_URL` est fourni par docker-compose). Ne jamais commiter `.env`.
2. Démarrer :

   ```bash
   docker compose up --build
   ```

- Front : http://localhost:5173
- API : http://localhost:8000 (Swagger : http://localhost:8000/docs)

Les migrations Alembic s'appliquent au démarrage du back. La base locale est vide au départ :
lancer une mise à jour à la main. Elle consomme 1 requête Tiingo par symbole (gratuit : 50/heure,
1 000/jour), donc pas plus d'un refresh complet par heure, tous environnements confondus :

```bash
curl -X POST -H "Authorization: Bearer <REFRESH_TOKEN>" http://localhost:8000/api/refresh
```

## API

| Méthode | Route | Rôle |
| --- | --- | --- |
| GET | `/api/quotes` | Dernière clôture de chaque symbole + variation vs la veille |
| GET | `/api/quotes/{symbol}/history` | Historique daily (5 ans) |
| POST | `/api/refresh` | Récupère les données Tiingo (token Bearer requis). Charge 5 ans pour un symbole nouveau, sinon seulement les séances manquantes |

## Production

- **Vercel** (root `front`) : `front/vercel.json` redirige `/api/*` vers Render.
- **Render** (root `back`) : variables d'environnement `DATABASE_URL` (URL Neon),
  `TIINGO_API_KEY`, `REFRESH_TOKEN`.
- **GitHub Actions** : `.github/workflows/daily-refresh.yml` appelle `POST /api/refresh` à 22:30 UTC
  du lundi au vendredi. Secret de dépôt requis : `REFRESH_TOKEN` (même valeur que sur Render).
  Lancement manuel possible depuis l'onglet Actions (« Run workflow »).
