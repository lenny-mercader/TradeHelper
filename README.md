# TradeHelper

- `front/` : React + TypeScript (Vite, npm, React Router, Recharts, Clerk), déployé sur Vercel
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
- Une action ouverte est mise à jour au plus une fois par jour à sa consultation, et chaque soir
  par le job planifié (toutes les actions déjà ouvertes au moins une fois).

## Comptes (Clerk)

- Connexion email + mot de passe ou Google, fenêtres Clerk en modale (en français).
- Le site se consulte sans compte ; la liste de suivi est **personnelle** et demande une connexion.
- Le back lit le cookie de session Clerk `__session` (même domaine grâce au proxy `/api`) et le
  vérifie avec le SDK Python Clerk, en n'acceptant que les origines de `AUTHORIZED_PARTIES`.
- On ne stocke que l'identifiant Clerk (table `watchlist_items`). Un webhook Clerk `user.deleted`
  efface la liste de l'utilisateur supprimé.
- Instance Clerk de **développement** pour l'instant (la production Clerk exige un nom de domaine).

## Lancer en local

1. Copier `back/.env.example` en `back/.env` et remplir `MASSIVE_API_KEY`, `CLERK_SECRET_KEY`
   (et `CLERK_WEBHOOK_SIGNING_SECRET` pour le webhook). Créer `front/.env.local` avec
   `VITE_CLERK_PUBLISHABLE_KEY=...`. `DATABASE_URL` est fourni par docker-compose. Ne jamais commiter
   ces fichiers.
2. Démarrer :

   ```bash
   docker compose up --build
   ```

3. Base locale vide : charger le catalogue US (~2 min) puis la clôture du marché :

   ```bash
   docker compose exec back python -m app.jobs catalog
   docker compose exec back python -m app.jobs daily
   ```

- Front : http://localhost:5173
- API : http://localhost:8000 (Swagger : http://localhost:8000/docs)

## API

| Méthode | Route | Rôle |
| --- | --- | --- |
| GET | `/api/search?q=` | Catalogue local (US + actions déjà ouvertes), complété par Yahoo |
| GET | `/api/instruments/{symbol}` | Dernière clôture (EUR + locale) ; charge l'historique à la 1re ouverture |
| GET | `/api/instruments/{symbol}/history` | Historique quotidien en EUR |
| GET | `/api/watchlist` | Liste de suivi de l'utilisateur connecté (401 sans session) |
| POST / DELETE | `/api/watchlist/{symbol}` | Suivre / ne plus suivre (session requise) |
| GET | `/api/market/movers` | Plus fortes hausses/baisses US de la dernière séance |
| GET | `/api/compare?symbols=A,B` | Perf 1 mois / 1 an / 5 ans, volatilité, plus haut/bas 52 sem. (EUR, 10 max) |
| POST | `/api/webhooks/clerk` | Webhook Clerk signé (suppression de compte) |

## Production

- **Vercel** (root `front`) : `front/vercel.json` redirige `/api/*` vers Render et sert
  `index.html` pour les routes du front.
- **Render** (root `back`) : variables `DATABASE_URL` (URL Neon), `MASSIVE_API_KEY`,
  `CLERK_SECRET_KEY`, `CLERK_WEBHOOK_SIGNING_SECRET`.
- **Vercel** : variable `VITE_CLERK_PUBLISHABLE_KEY`.
- **GitHub Actions** exécute les jobs (`python -m app.jobs`, connexion directe à Neon, pas de limite
  de durée Render). Secrets requis : `DATABASE_URL`, `MASSIVE_API_KEY`.
  - `daily-refresh.yml` : à 22:30 UTC du lundi au vendredi ;
  - `weekly-catalog.yml` : le dimanche à 06:00 UTC.
  Les deux se lancent aussi à la main (onglet Actions, « Run workflow »).
- Limite connue : Yahoo bloque parfois les IP de serveurs cloud. Dans ce cas les actions US
  restent servies par Massive (2 ans d'historique), les actions internationales non.
