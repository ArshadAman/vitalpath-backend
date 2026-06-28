# VitalPath Backend - Personal Health Navigation System

This is the backend API and background task execution stack for **VitalPath**, a preventive healthcare platform that continuously tracks lifestyle behaviors, medical histories, and health reports to predict health scores and recommend personalized actions.

---

## 1. Architecture Overview

The backend follows a **Modular "Feature-First" Architecture** (similar to Django applications), ensuring clean separation of concerns. Each domain feature resides in its own self-contained module under `app/features/` and encapsulates its own:
* **Models (`models.py`)**: SQLAlchemy database tables.
* **Schemas (`schemas.py`)**: Pydantic requests (deserializers) and responses (serializers).
* **Routes (`routes.py`)**: FastAPI endpoint routers.
* **Services (`services.py`)**: Pure Python domain business logic implementing the Single Responsibility Principle (SRP).
* **Tasks (`tasks.py`)**: Feature-specific Celery asynchronous tasks.

---

## 2. Tech Stack

* **Core Framework**: FastAPI (Asynchronous Python Web Framework).
* **Task Broker & Worker**: Celery + RabbitMQ (Message Broker).
* **Cache & Celery Backend**: Redis.
* **Database**: PostgreSQL (SQLAlchemy ORM).
* **Monitoring & Observability**: Prometheus (instrumentation scraping) + Grafana (dashboard metrics).
* **Containerization**: Docker & Docker Compose.

---

## 3. Directory Structure

```
backend/
├── app/
│   ├── core/                  # Core modules (global database session, logs config, Prometheus middleware)
│   ├── features/              # Feature modules (modular Django-like folders)
│   │   ├── auth/              # Registration, login, OTP dispatch, and JWT session tokens
│   │   ├── profile/           # Personal particulars, medical/family history, and lifestyle configuration
│   │   ├── timeline/          # Chronological health events log with search/filter features
│   │   ├── reports/           # PDF/image report upload, OCR parsing logic, and manual edits
│   │   ├── tracking/          # Step trackers, sleep, weight trends, and manual blood pressure inputs
│   │   ├── voice/             # Speech translation, transcription logs, and voice intent processing
│   │   ├── score/             # Overall Health Score (0-100) and biological Health Age calculators
│   │   ├── recommendations/   # Guidelines for exercise, nutrition, and preventive lab tests
│   │   ├── goals/             # Health goals trackers with automatic log-based evaluation
│   │   └── notifications/     # FCM push dispatcher task and notifications log
│   ├── main.py                # FastAPI entry router and lifespan initializer
│   ├── celery_app.py          # Celery worker instantiations
│   └── config.py              # AppSettings loader (Pydantic Settings)
├── tests/                     # Test configurations and features suites
│   ├── conftest.py            # SQLite session overrides and celery harness mocks
│   └── features/              # Feature integration tests
├── Dockerfile                 # Multi-stage image build setup (dev vs prod stages)
├── docker-compose.yml         # Dev services orchestrator
├── prometheus.yml             # Scraping endpoints mapping
└── requirements.txt           # Dependency lists
```

---

## 4. Configuration & Flag Mode

Configuration parameters are automatically loaded from `.env` (via Pydantic Settings). Changing `APP_ENV` changes the service modes:
* **Local Mode (`APP_ENV=local`)**:
  - Auto-creates SQLite/PostgreSQL schemas on startup.
  - Formats logs as human-readable dev logs.
  - Exposes debug tracebacks in HTTP error payloads.
* **Production Mode (`APP_ENV=production`)**:
  - Relies on database migration files.
  - Outputs structured JSON log streams.
  - Uses connection pools optimized for high concurrency.

---

## 4a. Mock OTP & Local Development

Because an external SMS gateway provider (such as Twilio) is not connected in the development sandbox, the system implements a **master OTP code: `0000`** (4 digits). 
* To authenticate via phone, register the phone number via the `/auth/register` signup endpoint first.
* Trigger a verification dispatch request via `/auth/otp/send`.
* Enter code `0000` via `/auth/otp/verify` to successfully authenticate and receive a JWT.

---

## 5. Local Setup & Running

### Requirements
* Docker Desktop installed.

### Steps
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Copy environment settings and adjust if needed:
   ```bash
   cp .env.example .env
   ```
3. Build and launch all services in detached mode:
   ```bash
   docker-compose up --build -d
   ```
4. Access the API documentation:
   - Swagger Documentation: `http://localhost:8000/docs`
   - Redoc Documentation: `http://localhost:8000/redoc`

---

## 6. Port Mappings (Network Encapsulation)

To adhere to security best practices, only the API Gateway and Grafana dashboard expose external ports to the host system. Other services communicate securely over the internal Docker bridge network:

| Service | Internal Port | Host Port | Purpose |
| :--- | :--- | :--- | :--- |
| **web** | `8000` | `8000` | FastAPI Server & Swagger Docs |
| **grafana** | `3000` | `8030` | Metrics Dashboards |
| **db** | `5432` | *Internal Only* | PostgreSQL Database |
| **redis** | `6379` | *Internal Only* | Caching & Task Results |
| **rabbitmq** | `5672` | *Internal Only* | Celery Task Broker |
| **prometheus** | `9090` | *Internal Only* | Metrics Scraping database |

---

## 7. Testing

Integration tests use an in-memory SQLite backend and mocked Celery worker calls to bypass MQ requirements, allowing for rapid test execution.

Run the test suite inside the running web container:
```bash
docker-compose exec web python -m pytest
```
