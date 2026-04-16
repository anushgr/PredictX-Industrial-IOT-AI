# PredictX Industrial AI

Industrial machine failure prediction dashboard built with Next.js App Router, TypeScript, Tailwind CSS, Chart.js, Radix UI primitives, Lucide icons, Framer Motion, Zustand, React Query, and Axios.

The frontend is currently focused on a single tracked asset, Conveyor-07, with three live sensors:

- Sound sensor
- Vibration sensor
- Temperature sensor

The app consumes JWT-protected FastAPI endpoints and reads backend data from the FastAPI service in this repository.

## Features

- JWT login flow with token storage in `localStorage`
- Single-machine dashboard for Conveyor-07
- Live telemetry cards for sound, vibration, and temperature
- Backend-driven analytics page with trend charts and summary metrics
- Predictive alerts, machine detail, users, and settings pages
- Responsive dark industrial UI with a sticky sidebar and header

## Project Structure

- `app/` - App Router pages and routes
- `components/` - Dashboard shell, charts, auth, and UI primitives
- `hooks/` - React Query data hooks and telemetry hooks
- `lib/` - Chart registration and utilities
- `services/api.ts` - Axios client and backend API wrappers
- `store/` - UI state store for sidebar behavior and plant selection
- `types/` - Shared TypeScript models

## Development

Install dependencies:

```bash
npm install
```

Run the frontend:

```bash
npm run dev
```

By default the app runs on `http://localhost:3000`. If that port is busy, Next.js may choose another available port.

## Backend

The frontend expects the FastAPI backend to run at `http://localhost:8000`.

Backend API endpoints used by the frontend include:

- `POST /api/login`
- `GET /api/machines`
- `GET /api/sensors/live`
- `GET /api/sensors/history`
- `GET /api/predict/failure`
- `GET /api/predict/alerts`
- `GET /api/analytics`
- `GET /health`
- `WS /ws/telemetry`

## Demo Login

Use the login page at `/login` with:

- Email: `ava@predictx.ai`
- Password: `admin123`

The backend returns a JWT access token, which the frontend stores as `predictx_token` and attaches to protected requests.

## Notes

- The dashboard is intentionally scoped to one machine and three sensors.
- Analytics, telemetry, and predictions are backed by the FastAPI service.
- The frontend is optimized for a dark, industrial SaaS look and responsive layouts.
