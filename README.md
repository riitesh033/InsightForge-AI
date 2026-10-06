# InsightForge AI - README

## Your AI Data Analyst

InsightForge AI is an intelligent web-based dataset analysis platform that automates data quality assessment, statistical analysis, and insight generation. Upload CSV or Excel files (`.csv`, `.xls`, `.xlsx`) for professional analysis and AI-powered insights.

![Dashboard](docs/images/dashboard.png)

## Features

### 📊 Automated Data Analysis
- **Data Profiling**: Automatic detection of rows, columns, data types, and memory usage
- **Quality Scoring**: Deterministic composite score (0-100) based on missing cells, duplicate rows, and potential outliers
- **Missing Value Detection**: Identify and analyze missing data patterns
- **Duplicate Detection**: Find and quantify duplicate rows
- **Outlier Detection**: IQR-based outlier identification for numerical columns
- **Statistical Summary**: Mean, median, standard deviation, quartiles, and more
- **Correlation Analysis**: Pearson correlation matrix for numerical features

On upload, InsightForge AI automatically profiles uploaded datasets and
calculates row/column counts, data types, missing values, duplicate records,
descriptive statistics, correlations, IQR-based potential outliers, a
deterministic quality score, and data-driven recommendations. The AI layer
then converts the verified profile into a natural-language explanation.

The quality score starts at 100 and subtracts up to 45 points for missing
cells (the missing-cell share of all cells), up to 25 points for duplicate
rows (the duplicate-row share of records), and up to 30 points for potential
outliers (the outlier share of observed numeric values). Each penalty is
proportional to its measured share and capped at its stated maximum; the
result is rounded to the nearest whole number. Empty datasets score 0 because
there are no records to assess. Duplicate detection retains the existing
behavior of ignoring ID-like columns when identifying otherwise repeated
records. These fixed weights make the score deterministic for unchanged
input; it is an overview metric, not a statistical guarantee.

### 🤖 AI-Powered Insights
- **Automatic Insights**: AI-generated findings about patterns, anomalies, and recommendations
- **Dataset Chat**: Ask natural language questions about your data
- **Smart Recommendations**: Data cleaning suggestions with preview

### 📁 Dataset Management
- **Multi-format Support**: CSV and Excel (.xls, .xlsx) file uploads
- **Secure Storage**: User-isolated datasets with ownership enforcement
- **Version Control**: Original and cleaned dataset versions
- **Search & Filter**: Find datasets quickly with search functionality

### 📈 Visualizations
- Histograms and distribution charts
- Box plots for outlier visualization
- Bar charts for categorical frequencies
- Correlation heatmaps
- Missing value charts
- Datatype distribution charts

### 📄 Professional Reports
- One-click PDF report generation (Pro and Business)
- Comprehensive analysis summaries
- AI insights and recommendations
- Professional formatting for stakeholders

### 🧹 Data Cleaning
- Available on Pro and Business
- Remove duplicate rows
- Fill missing values (mean/median/mode strategies)
- Drop rows with missing values
- Normalize categorical values
- Preview changes before applying
- Download cleaned datasets

### 💳 Plan limits
Plan limits are enforced by the backend using the Stripe-confirmed subscription
state; client-side plan values are informational only.

| Plan | Datasets | Maximum file size | AI chat queries per UTC calendar month |
| --- | ---: | ---: | ---: |
| Free | 3 | 10 MB | 10 |
| Pro | Unlimited | 100 MB | 500 |
| Business | Unlimited | 500 MB | Unlimited |

AI chat usage is counted when the user message is saved, including attempts
where the AI provider is unavailable. Professional PDF reports and data
cleaning require Pro or Business.

### 🔒 Security & Authentication
- Secure user registration and login
- JWT token-based authentication
- Protected routes and API endpoints
- Dataset ownership verification

### 🎨 User Experience
- Responsive design (desktop, tablet, mobile)
- Light/dark theme toggle
- Loading states and error handling
- Toast notifications
- Intuitive navigation

## Quick Start

### Prerequisites

- **Node.js** 18+
- **Python** 3.10+
- **PostgreSQL** 14+
- An AI provider configured for the backend (Gemini, OpenRouter, or Ollama; optional for non-AI workflows)

### Installation

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd InsightForge-AI
```

#### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements/base.txt

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
# DATABASE_URL=postgresql://user:password@localhost:5432/insightforge
# SECRET_KEY=your-secret-key-change-in-production
# FRONTEND_URL=http://localhost:5173
# OLLAMA_BASE_URL=http://host.docker.internal:11434
# OLLAMA_MODEL=qwen3:8b

# Create database
createdb insightforge
# Or using psql:
# psql -U postgres -c "CREATE DATABASE insightforge;"

# Run migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`  
API Documentation (Swagger): `http://localhost:8000/docs`

#### 3. Setup Frontend

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env

# Start development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

#### 4. Access the Application

1. Open browser to `http://localhost:5173`
2. Register a new account
3. Login with your credentials
4. Upload a CSV or Excel (`.xls`/`.xlsx`) dataset
5. View automatic analysis and AI insights

### Docker Deployment

```bash
# Build and start all services
# Copy the templates first, then set unique local values.
cp .env.example .env
cp backend/.env.example backend/.env
docker compose up --build

# Access application
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# Database: localhost:5432
```

Set `POSTGRES_PASSWORD` in the root `.env` file to a unique URL-safe local
password before starting Compose. Set `SECRET_KEY` in `backend/.env` to a
random value; optional AI, SMTP, and Stripe integrations remain unconfigured
until their credentials and settings are supplied.

The Compose configuration is for development and uses file watching/hot reload.
The backend and frontend Dockerfiles also provide production targets with no
development server or reload behavior:

```bash
docker build --target production -t insightforge-backend ./backend
docker build --target production \
  --build-arg VITE_API_URL=https://your-api.example.com/api/v1 \
  -t insightforge-frontend ./frontend
```

## Usage Guide

### Uploading a Dataset

1. Navigate to **Datasets** from the sidebar
2. Click **Upload Dataset** button
3. Select CSV or Excel file from your computer
4. Wait for upload and automatic analysis to complete
5. Dataset appears in your dataset list

### Analyzing a Dataset

1. Click on any dataset card from the Datasets page
2. Analysis runs automatically upon upload
3. View comprehensive analysis including:
   - Overview (rows, columns, quality score)
   - Data Quality metrics
   - Column-by-column analysis
   - Visualizations
   - AI Insights
   - Cleaning Recommendations

### Chatting with Your Data

1. Open a dataset
2. Navigate to **AI Chat** tab
3. Ask questions like:
   - "How many rows are there?"
   - "Which column has the most missing values?"
   - "What is the average salary?"
   - "Are there any outliers?"
   - "What cleaning do you recommend?"
4. AI responds with context-aware answers

### Generating Reports

1. Open an analyzed dataset
2. Click **Generate Report** button
3. PDF report downloads automatically
4. Report includes all analysis sections and AI insights

### Cleaning Data

1. Open dataset analysis page
2. Review cleaning recommendations
3. Click **Preview Cleaning**
4. Review proposed changes
5. Click **Apply Cleaning** to create cleaned version
6. Download cleaned dataset

## Technology Stack

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tooling
- **Tailwind CSS** - Styling
- **Recharts** - Data visualizations
- **Axios** - HTTP client
- **React Router** - Navigation

### Backend
- **FastAPI** - Web framework
- **Python 3.10+** - Programming language
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Alembic** - Migrations
- **Pandas** - Data processing
- **ReportLab** - PDF generation

### AI
- **Gemini** - Primary provider by default
- **OpenRouter** - Fallback provider
- **Ollama** - Local fallback (`qwen3:8b` by default)

## Project Structure

```
InsightForge-AI/
├── frontend/
│   ├── src/
│   │   ├── api/           # API client modules
│   │   ├── components/    # Reusable components
│   │   ├── context/       # React contexts
│   │   ├── hooks/         # Custom hooks
│   │   ├── layouts/       # Page layouts
│   │   ├── pages/         # Route pages
│   │   ├── services/      # Business logic
│   │   ├── types/         # TypeScript types
│   │   ├── utils/         # Utilities
│   │   └── lib/           # Library configs
│   ├── package.json
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Core utilities
│   │   ├── crud/          # Database operations
│   │   ├── db/            # Database config
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── main.py        # Entry point
│   ├── alembic/           # Migrations
│   ├── requirements/      # Dependencies
│   └── Dockerfile
├── docs/                  # Documentation
├── docker-compose.yml
├── README.md
└── .env.example
```

## Environment Variables

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/insightforge` |
| `SECRET_KEY` | JWT signing key (change in production!) | `your-secret-key-change-in-production` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:5173` |
| `DATASET_STORAGE_DIR` | Directory for uploaded datasets | `app/uploads/datasets` |
| `OLLAMA_BASE_URL` | Ollama API URL | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | AI model name | `qwen3:8b` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `60` |
| `DEBUG` | Debug mode | `True` |
| `ENVIRONMENT` | Environment name | `development` |
| `STUDENT_VERIFICATION_STORAGE_DIR` | Private directory for student proof documents | `private_uploads/student_verification` |

Student verification evidence is stored outside the frontend/static asset tree
and is served only through authenticated admin endpoints. On Render or another
ephemeral-filesystem host, set `STUDENT_VERIFICATION_STORAGE_DIR` to a mounted
persistent disk directory (for example,
`/var/data/insightforge/student-verification`) so documents survive deploys.
Restrict filesystem access to the backend service.
Reviewed proof files are deleted after 90 days when student/admin verification
API activity triggers lazy cleanup; there is no periodic cleanup scheduler yet.
Current upload validation checks size, declared media type, and file signature;
an antivirus scanner is not configured.

Uploaded CSV/XLS/XLSX files are stored under `DATASET_STORAGE_DIR`; the default
is `backend/app/uploads/datasets` for local development and Docker Compose. On
Render, service filesystems are ephemeral. To keep uploads available after
restarts and deploys, attach a Persistent Disk mounted at `/var/data` and set
`DATASET_STORAGE_DIR=/var/data/insightforge/datasets`. New database records
store only the generated filename; existing absolute or relative file paths
continue to resolve by filename under the configured storage root. Dataset
metadata does not contain original file contents, so a missing file cannot be
reconstructed from the database.

Student verification proof documents use the separate
`STUDENT_VERIFICATION_STORAGE_DIR`. For persistence, set it to
`/var/data/insightforge/student-verification` on that same mounted disk. Do not
put private proof documents in a public/static directory.

### Administrator account management

Admin access is controlled by the database-backed `users.is_superuser` field.
The field defaults to false for registered and Google-created accounts. Admins
sign in at `/admin/login`; the dedicated form calls
`POST /api/v1/auth/admin/login`, which uses the normal password hash and JWT
implementation and refuses accounts without current database admin status.
There is no automatic admin bootstrap.

From the backend service shell, run `python -m app.scripts.create_admin`.
The command prompts for the existing account email and hidden password entry
(plus password confirmation), then sets the new password using the existing
hashing implementation and enables `is_superuser`. It will not create a user.
To check an account, run `python -m app.scripts.create_admin --check`; enter
the account email when prompted. The check never requests or changes a password.

### Frontend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |

## API Documentation

Once the backend is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login user |
| GET | `/api/v1/auth/google/login` | Start Google OAuth login |
| POST | `/api/v1/auth/forgot-password` | Request a password reset |
| POST | `/api/v1/auth/reset-password` | Reset a password |
| POST | `/api/v1/auth/admin/login` | Admin-only credential login |
| GET | `/api/v1/users/me` | Get current user |
| POST | `/api/v1/datasets/upload` | Upload a dataset |
| GET | `/api/v1/datasets` | List the current user's datasets |
| GET | `/api/v1/datasets/{dataset_id}` | Get an owned dataset |
| PATCH | `/api/v1/datasets/{dataset_id}` | Rename an owned dataset |
| DELETE | `/api/v1/datasets/{dataset_id}` | Delete an owned dataset |
| GET | `/api/v1/datasets/{dataset_id}/download` | Download the original dataset |
| GET | `/api/v1/student-verification/me` | Get student verification status |
| POST | `/api/v1/student-verification/applications` | Submit student verification evidence |
| POST | `/api/v1/student-verification/applications/{application_id}/withdraw` | Withdraw a pending application |
| GET | `/api/v1/admin/student-verifications` | Admin-only application review queue |
| GET | `/api/v1/admin/student-verifications/{id}/proof` | Admin-only proof document download |
| POST | `/api/v1/admin/student-verifications/{id}/approve` | Admin-only approval and one-year Pro access |
| POST | `/api/v1/admin/student-verifications/{id}/reject` | Admin-only rejection with reason |
| GET | `/api/v1/analysis/{dataset_id}` | Get analysis results |
| GET | `/api/v1/analysis/{dataset_id}/explanation` | Get a cached AI explanation or generate one from the verified profile |
| GET | `/api/v1/analysis/{dataset_id}/report` | Generate/download an analysis PDF |
| GET | `/api/v1/reports/` | List reports for the current user |
| GET | `/api/v1/reports/{dataset_id}/pdf` | Download a dataset PDF report |
| GET/POST | `/api/v1/chat/{dataset_id}/sessions` | List/create dataset chat sessions |
| GET/DELETE | `/api/v1/chat/sessions/{session_id}` | Read/delete an owned chat session |
| POST | `/api/v1/chat/{dataset_id}` | Send a message about an owned dataset |
| POST | `/api/v1/cleaning/{dataset_id}/preview` | Preview cleaning |
| POST | `/api/v1/cleaning/{dataset_id}/apply` | Apply cleaning |
| GET | `/api/v1/cleaning/{dataset_id}/download` | Download the cleaned dataset |
| GET | `/api/v1/payments/plans` | List available plans |
| POST | `/api/v1/payments/create-checkout` | Start paid-plan checkout |
| GET | `/api/v1/payments/subscription` | Read the current user's subscription |
| POST | `/api/v1/payments/cancel` | Request subscription cancellation |
| GET | `/api/v1/payments/history` | Read the current user's payment history |
| GET | `/api/v1/payments/invoices/{invoice_id}` | Download an owned invoice |
| POST | `/api/v1/payments/webhook` | Process a Stripe-signed webhook |

The API's OpenAPI schema at `/openapi.json` is the source of truth for all
routes and request/response schemas.

## Testing

### Backend Tests

```bash
cd backend
pytest -q
```

### Frontend Build & Type Check

```bash
cd frontend
npm run build
npm run lint
```

## Troubleshooting

### Database Connection Error

Ensure PostgreSQL is running and credentials are correct:

```bash
# Check PostgreSQL status
pg_isready

# Test connection
psql -U postgres -d insightforge
```

### AI Features Not Working

1. Ensure Ollama is installed and running:
   ```bash
   ollama serve
   ```

2. Pull the required model:
   ```bash
   ollama pull qwen3:8b
   ```

3. Verify Ollama is accessible:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Port Already in Use

Change ports in configuration files:

- Backend: Edit `uvicorn` command with different `--port`
- Frontend: Edit `vite.config.ts` with different port
- Database: Change port in `DATABASE_URL`

### Migration Status

Inspect migration state and apply forward migrations:

```bash
cd backend
alembic current
alembic heads
alembic history
alembic upgrade head
```

The current repository migration head is
`20261001_student_verification`. Back up the database before any migration
operation. Do not downgrade to `base` or reset an existing database to
troubleshoot a migration problem.

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Set `DEBUG=False` in backend
- [ ] Configure CORS for production domain
- [ ] Use HTTPS/TLS
- [ ] Enable rate limiting
- [ ] Use environment variables for secrets
- [ ] Regular dependency updates
- [ ] Database backups configured

### Recommended Infrastructure

- **Frontend**: Vercel, Netlify, or Cloudflare Pages
- **Backend**: Railway, Render, AWS ECS, or GCP Cloud Run
- **Database**: Managed PostgreSQL (AWS RDS, Supabase, Neon)
- **AI**: Self-hosted Ollama or cloud LLM provider

For Render, attach a Persistent Disk to the backend and set
`DATASET_STORAGE_DIR` and `STUDENT_VERIFICATION_STORAGE_DIR` to directories
under its configured mount path (for example `/var/data/insightforge/datasets`
and `/var/data/insightforge/student-verification` for a disk mounted at
`/var/data`). Render's service filesystem is ephemeral without that disk. The
repository does not include a Render deployment manifest, so disk attachment
and environment values must be configured in the Render service settings.

## Limitations

1. **Dataset Size**: Performance may degrade with files >100MB
2. **AI Availability**: Requires an available configured AI provider; graceful degradation is implemented
3. **Concurrent Users**: Single-user per dataset (no real-time collaboration)
4. **Analytics Scope**: Descriptive statistics only (no predictive modeling)

## Future Enhancements

- [ ] Multiple AI model support
- [ ] Time series analysis
- [ ] Dataset joining/blending
- [ ] Custom transformation rules
- [ ] Scheduled report generation
- [ ] Team collaboration features
- [ ] Public API access
- [ ] Additional export formats (JSON, Parquet)

## License

This project is created as an academic submission for B.Sc. Computer Science.

## Contributing

This is an academic project. For questions or suggestions, please contact the development team.

## Acknowledgments

- FastAPI team for the excellent web framework
- React team for the UI library
- Ollama for local LLM support
- All open-source contributors

---

**Built with ❤️ for data-driven insights**
