# 🚀 Development
## Frontend
### Install dependencies
```bash
cd frontend
yarn
```
### Run development server
```bash
cd frontend
yarn dev
```

## Backend
### Install dependencies
> Requires Python3 and Poetry

```bash
cd backend
poetry install
```

### Run development server
```bash
cd backend
poetry run flask -A backend run -p 5001 --reload
```

### Caching
Uses `requests_cache` to cache API requests. Cache can use sqlite (less performant, sometimes buggy) or Redis as backend.

To use Redis, start the Docker container from the root of the project:
```bash
docker compose up -d
```
