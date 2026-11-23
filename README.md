# InsightIQ

AI-Powered Data Analytics and Business Intelligence Platform

## Overview

InsightIQ is a sophisticated analytical workspace that transforms raw datasets into meaningful business intelligence through natural language interaction, advanced analytics, and professional visualizations.

## Features

- **Natural Language Analytics** - Ask questions about your data in plain English
- **Automated Data Profiling** - Comprehensive statistical analysis of uploaded datasets
- **Interactive Visualizations** - 18+ chart types with intelligent selection
- **Advanced Analytics** - Forecasting, anomaly detection, correlation analysis
- **Executive Reporting** - Professional PDF, Excel, and CSV exports
- **Multi-Dataset Workspace** - Manage and switch between multiple datasets
- **Conversational Context** - Follow-up questions maintain analytical context

## Tech Stack

### Frontend
- React 18 + TypeScript + Vite
- Tailwind CSS + shadcn/ui (Radix UI)
- TanStack Query + TanStack Table
- Apache ECharts + Framer Motion
- Zustand for state management

### Backend
- FastAPI + Python 3.11+
- Pandas + NumPy + SciPy + Scikit-learn
- DuckDB for analytical SQL
- OpenAI-compatible LLM integration

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm 9+

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
insightiq/
├── frontend/           # React + TypeScript application
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Page components
│   │   ├── hooks/      # Custom React hooks
│   │   ├── services/   # API services
│   │   ├── stores/     # Zustand stores
│   │   ├── types/      # TypeScript types
│   │   └── utils/      # Utilities
│   └── package.json
├── backend/            # FastAPI application
│   ├── app/
│   │   ├── api/        # API routes
│   │   ├── core/       # Core configuration
│   │   ├── models/     # Database models
│   │   ├── schemas/    # Pydantic schemas
│   │   ├── services/   # Business logic
│   │   └── utils/      # Utilities
│   ├── tests/
│   └── requirements.txt
├── docs/
├── .gitignore
└── README.md
```

## Development

### Running Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test
```

### Linting

```bash
# Backend
cd backend
ruff check .

# Frontend
cd frontend
npm run lint
```

## Environment Variables

See `backend/.env.example` for all configuration options.

Key variables:
- `LLM_PROVIDER` - LLM provider (openai-compatible, nvidia-nim, groq)
- `LLM_API_KEY` - API key for LLM provider
- `LLM_MODEL` - Model to use
- `DATABASE_URL` - PostgreSQL connection string
- `MAX_FILE_SIZE_MB` - Maximum upload size

## License

MIT