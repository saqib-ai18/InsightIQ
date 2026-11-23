# InsightIQ Environment Variables Reference

This document lists all environment variables required for InsightIQ deployment.

## Backend Environment Variables

### Application
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `APP_NAME` | Application name | `InsightIQ` | No | No |
| `APP_VERSION` | Application version | `0.1.0` | No | No |
| `DEBUG` | Enable debug mode | `false` | No | No |
| `HOST` | Server host | `0.0.0.0` | No | No |
| `PORT` | Server port | `8000` | No | No |

### Security
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `SECRET_KEY` | JWT signing secret (generate with `openssl rand -hex 32`) | - | **Yes** | **Yes** |
| `ALGORITHM` | JWT algorithm | `HS256` | No | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry in minutes | `30` | No | No |

### CORS
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173,http://localhost:3000` | **Yes** | No |

### Database
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./data/insightiq.db` | **Yes** | **Yes** |
| `DUCKDB_PATH` | DuckDB file path | `./data/analytics.duckdb` | No | No |

### File Upload
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `UPLOAD_DIR` | Local upload directory | `./uploads` | No | No |
| `MAX_FILE_SIZE_MB` | Maximum file size in MB | `100` | No | No |
| `ALLOWED_EXTENSIONS` | Comma-separated allowed extensions | `csv,xlsx,xls,json,parquet` | No | No |

### AI/LLM Configuration
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `LLM_PROVIDER` | Provider: `openai-compatible`, `nvidia-nim`, `groq` | `openai-compatible` | No | No |
| `LLM_API_KEY` | API key for LLM provider | - | **Yes** | **Yes** |
| `LLM_BASE_URL` | API base URL | `https://api.openai.com/v1` | No | No |
| `LLM_MODEL` | Model name | `gpt-4o-mini` | No | No |
| `LLM_TEMPERATURE` | Sampling temperature | `0.1` | No | No |
| `LLM_MAX_TOKENS` | Max output tokens | `4096` | No | No |
| `LLM_TIMEOUT` | Request timeout in seconds | `60` | No | No |

### Data Processing
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `DEFAULT_CHUNK_SIZE` | Default chunk size for processing | `10000` | No | No |
| `PROFILING_SAMPLE_SIZE` | Sample size for profiling | `10000` | No | No |
| `QUERY_TIMEOUT_SECONDS` | SQL query timeout | `30` | No | No |

### Logging
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `LOG_LEVEL` | Log level | `INFO` | No | No |
| `LOG_FORMAT` | Log format | `json` | No | No |

### Cloudflare R2 Storage
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `R2_ACCOUNT_ID` | Cloudflare account ID | - | **Yes** | **Yes** |
| `R2_ACCESS_KEY_ID` | R2 access key ID | - | **Yes** | **Yes** |
| `R2_SECRET_ACCESS_KEY` | R2 secret access key | - | **Yes** | **Yes** |
| `R2_BUCKET_NAME` | R2 bucket name | `insightiq-datasets` | No | No |
| `R2_PUBLIC_URL` | Public URL for R2 (optional) | - | No | No |

### NVIDIA NIM Rate Limiting
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `NVIDIA_RATE_LIMIT_REQUESTS` | Max requests per window | `60` | No | No |
| `NVIDIA_RATE_LIMIT_WINDOW_SECONDS` | Rate limit window in seconds | `60` | No | No |

### File Processing Limits
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `MAX_DATASET_ROWS` | Maximum rows per dataset | `100000` | No | No |
| `MAX_CONCURRENT_ANALYTICS` | Max concurrent analytics operations | `3` | No | No |

---

## Frontend Environment Variables

### API Configuration
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `VITE_API_BASE_URL` | Backend API base URL | `/api` | **Yes** | No |

### Optional Analytics
| Variable | Description | Default | Required | Sensitive |
|----------|-------------|---------|----------|-----------|
| `VITE_GA_ID` | Google Analytics ID | - | No | No |

---

## Environment-Specific Configurations

### Development (.env.local)
```bash
# Backend
DEBUG=true
DATABASE_URL=sqlite:///./data/insightiq.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
LLM_PROVIDER=openai-compatible
LLM_API_KEY=your-dev-key
R2_ACCOUNT_ID=
R2_ACCESS_KEY_ID=
R2_SECRET_ACCESS_KEY=

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api
```

### Staging
```bash
# Backend
DEBUG=false
DATABASE_URL=postgresql://user:pass@staging-neon-host/db
CORS_ORIGINS=https://staging-insightiq.pages.dev
LLM_PROVIDER=nvidia-nim
LLM_API_KEY=your-staging-key
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key

# Frontend
VITE_API_BASE_URL=https://staging-api.onrender.com/api
```

### Production
```bash
# Backend
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-neon-host/db?sslmode=require
CORS_ORIGINS=https://insightiq.pages.dev,https://www.insightiq.app
LLM_PROVIDER=nvidia-nim
LLM_API_KEY=your-prod-key
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_PUBLIC_URL=https://pub-xxx.r2.dev
SECRET_KEY=your-generated-secret-key

# Frontend
VITE_API_BASE_URL=https://api.insightiq.app/api
```

---

## Secret Generation

### Generate SECRET_KEY
```bash
openssl rand -hex 32
```

### Generate API Keys
```bash
# For R2
# Create in Cloudflare Dashboard → R2 → Manage R2 API tokens

# For NVIDIA NIM
# Create at https://integrate.api.nvidia.com
```

---

## Variable Validation Checklist

Before deploying, verify:

- [ ] `SECRET_KEY` is set and unique per environment
- [ ] `DATABASE_URL` points to correct Neon project
- [ ] `CORS_ORIGINS` includes exact frontend URL(s)
- [ ] `LLM_API_KEY` is valid NVIDIA NIM key
- [ ] `R2_*` credentials have correct bucket permissions
- [ ] `VITE_API_BASE_URL` matches deployed backend URL
- [ ] `DEBUG=false` in production
- [ ] No `.env` files committed to git
- [ ] All secrets stored in platform secret managers (Render, Cloudflare, GitHub)

---

## Platform-Specific Configuration

### Render (Backend)
Set environment variables in Render dashboard → Service → Environment.

### Cloudflare Pages (Frontend)
Set in Pages project → Settings → Environment variables.

### Neon (Database)
Connection string provided in Neon dashboard → Connection Details.

### Cloudflare R2
Create in R2 dashboard → Manage R2 API tokens.

### NVIDIA NIM
Create at https://integrate.api.nvidia.com → API Keys.

---

## Security Notes

1. **Never commit `.env` files** - They are in `.gitignore`
2. **Rotate secrets regularly** - Especially `SECRET_KEY` and API keys
3. **Use platform secret managers** - Don't hardcode in code
4. **Principle of least privilege** - Grant minimal permissions to API keys
5. **Monitor for leaks** - Use GitHub secret scanning