# AutoModerate Chat Prototype

Прототип публичного чата с серверной гибридной модерацией (`rules -> ML -> decision`).

## Запуск одной командой (Docker Compose)

Из корня проекта:

```bash
docker compose up --build
```

После запуска:

- frontend: `http://localhost:5173`
- backend API: `http://localhost:5000`
- На первом запуске backend скачает `cointegrated/rubert-tiny-toxicity` и будет работать на CPU.
- Кэш модели сохраняется в Docker volume (`HF_HOME=/app/data/hf-home`), повторно качать не нужно.
- Автоматически создаются 3 демо-учетки (и сбрасываются при каждом старте backend):
  - `demo_user` / `demo12345` (роль `user`)
  - `demo_moderator` / `demo12345` (роль `moderator`)
  - `demo_admin` / `demo12345` (роль `admin`)

Остановка:

```bash
docker compose down
```

С удалением тома SQLite:

```bash
docker compose down -v
```

Если после изменения Docker-файлов контейнеры уже были запущены:

```bash
docker compose down
docker compose up --build
```

## Что поднято в compose

- `backend`:
  - Flask + Flask-SocketIO
  - SQLite в томе `backend_data` (`/app/data/chat.db`)
  - `ML_MODEL=cointegrated/rubert-tiny-toxicity` (модель загружается при первом старте)
- `frontend`:
  - сборка Vue/Vite
  - Nginx, который:
    - отдает SPA
    - проксирует `/api/*` и `/socket.io/*` в `backend`

## Локальный запуск без Docker

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
python run.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Проверки

### Backend tests

```bash
cd backend
python -m pytest -q
```

### Coverage

```bash
cd backend
python -m pytest --cov=app --cov-report=term-missing -q
```

### Frontend build

```bash
cd frontend
npm run build
```

## Примечания

- `db.create_all()` выполняется при старте приложения.
- `Flask-Migrate` подключен, но миграции не инициализированы.
- Чтобы отключить ML и использовать fallback, замените в `docker-compose.yml`:
  - `ML_MODEL: cointegrated/rubert-tiny-toxicity`
  - на `ML_MODEL: disabled`
