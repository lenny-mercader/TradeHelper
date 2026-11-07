# TradeHelper

- `front/` : React + TypeScript (Vite), npm
- `back/` : Python 3.15 + FastAPI, Poetry

## Lancer

```bash
docker compose up --build
```

- Front : http://localhost:5173
- API : http://localhost:8000 (doc Swagger : http://localhost:8000/docs)

Le front appelle l'API via `/api/...`, que le serveur Vite redirige vers le service `back`.
Le hot reload est actif des deux côtés.
