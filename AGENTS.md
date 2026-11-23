# InsightIQ Development Agents

This document defines the specialized agents and their responsibilities for the InsightIQ project.

## Agent Types

### 1. Backend Engineer
**Responsibilities:**
- FastAPI application architecture
- API endpoint design and implementation
- Database models and migrations
- Data ingestion and processing pipelines
- Analytical engine implementation
- LLM integration layer
- Security and authentication
- Performance optimization

**Key Files:**
- `backend/app/main.py`
- `backend/app/api/`
- `backend/app/services/`
- `backend/app/core/`
- `backend/app/schemas/`

### 2. Frontend Engineer
**Responsibilities:**
- React + TypeScript application
- Component architecture and design system
- State management (TanStack Query, Zustand)
- Data visualization integration (ECharts)
- Real-time chat interface
- Dashboard and data explorer
- Responsive design and accessibility

**Key Files:**
- `frontend/src/components/`
- `frontend/src/pages/`
- `frontend/src/hooks/`
- `frontend/src/services/`
- `frontend/src/stores/`

### 3. Data Engineer
**Responsibilities:**
- Data ingestion and validation
- Automated data profiling
- Statistical computation engine
- DuckDB analytical queries
- Data quality assessment
- Export pipelines (PDF, Excel, CSV)

**Key Files:**
- `backend/app/services/ingestion/`
- `backend/app/services/profiling/`
- `backend/app/services/analytics/`
- `backend/app/services/visualization/`
- `backend/app/services/reporting/`

### 4. AI/ML Engineer
**Responsibilities:**
- LLM provider abstraction layer
- Structured output parsing
- Tool/function calling implementation
- Conversation context management
- Prompt engineering for analytics
- Analytical operation validation
- Forecasting and anomaly detection models

**Key Files:**
- `backend/app/services/ai/`
- `backend/app/schemas/ai.py`

### 5. QA Engineer
**Responsibilities:**
- Test strategy and implementation
- Backend unit/integration tests (pytest)
- Frontend component tests (Vitest + RTL)
- E2E tests (Playwright)
- Analytical correctness verification
- Performance benchmarking

**Key Files:**
- `backend/tests/`
- `frontend/src/**/*.test.tsx`

## Development Workflow

### Phase Gates
Each phase must pass:
1. All tests pass
2. Linting passes
3. Type checking passes
4. Manual verification of key features

### Code Review Standards
- All PRs require review
- Analytical logic must be verified with known datasets
- Security-sensitive changes require additional review
- UI changes must be tested across breakpoints

## Commands

### Backend
```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload          # Development server
pytest                                 # Run tests
ruff check .                           # Lint
ruff check . --fix                     # Auto-fix lint
mypy app/                              # Type check
black app/                             # Format
```

### Frontend
```bash
cd frontend
npm run dev                            # Development server
npm run build                          # Production build
npm run lint                           # Lint
npm run test                           # Unit tests
npm run test:ui                        # Test UI
```

## Architecture Decisions

### ADR 001: Monorepo Structure
Single repository with separate frontend/backend directories for simplified deployment and shared tooling.

### ADR 002: DuckDB for Analytics
DuckDB provides fast analytical SQL without separate infrastructure. Used for read-only analytical queries.

### ADR 003: LLM Provider Abstraction
Support multiple LLM providers (OpenAI-compatible, NVIDIA NIM, Groq) through unified interface.

### ADR 004: No Arbitrary Code Execution
LLM never executes raw Python. All operations go through validated analytical tool interface.

### ADR 005: Dark-First Design System
Professional dark theme with optional light mode. Tailwind CSS with custom design tokens.

## Quality Standards

### Analytical Correctness
- All calculations verified against known datasets
- Statistical methods documented with references
- Edge cases handled (empty data, single values, NaN)

### Security
- File type validation on upload
- Size limits enforced
- SQL injection prevention via parameterized queries
- No eval/exec of AI-generated code
- Secrets in environment variables only

### Performance
- Lazy loading for large datasets
- Server-side pagination for data tables
- Caching for expensive computations
- Query timeouts enforced

## Testing Requirements

### Minimum Coverage
- Backend: 80% unit test coverage
- Frontend: 70% component test coverage
- Critical paths: 100% coverage (auth, data processing, AI tools)

### Test Data
- Use synthetic datasets with known analytical results
- Include edge cases: missing values, duplicates, mixed types
- Test datasets version-controlled in `tests/fixtures/`