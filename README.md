# InsightForge AI - README

## Your AI Data Analyst

InsightForge AI is an intelligent web-based dataset analysis platform that automates data quality assessment, statistical analysis, and insight generation. Upload your CSV or Excel files and get instant professional analysis with AI-powered insights.

![Dashboard](docs/images/dashboard.png)

## Features

### 📊 Automated Data Analysis
- **Data Profiling**: Automatic detection of rows, columns, datatypes, and memory usage
- **Quality Scoring**: Composite score (0-100) based on completeness, uniqueness, validity, and consistency
- **Missing Value Detection**: Identify and analyze missing data patterns
- **Duplicate Detection**: Find and quantify duplicate rows
- **Outlier Detection**: IQR-based outlier identification for numerical columns
- **Statistical Summary**: Mean, median, standard deviation, quartiles, and more
- **Correlation Analysis**: Pearson correlation matrix for numerical features

### 🤖 AI-Powered Insights
- **Automatic Insights**: AI-generated findings about patterns, anomalies, and recommendations
- **Dataset Chat**: Ask natural language questions about your data
- **Smart Recommendations**: Data cleaning suggestions with preview

### 📁 Dataset Management
- **Multi-format Support**: CSV and Excel (.xlsx) file uploads
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
- One-click PDF report generation
- Comprehensive analysis summaries
- AI insights and recommendations
- Professional formatting for stakeholders

### 🧹 Data Cleaning
- Remove duplicate rows
- Fill missing values (mean/median/mode strategies)
- Drop rows with missing values
- Normalize categorical values
- Preview changes before applying
- Download cleaned datasets

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
- **Ollama** (optional, for AI features)

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
pip install -r requirements.txt

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
4. Upload a CSV or Excel dataset
5. View automatic analysis and AI insights

### Docker Deployment

```bash
# Build and start all services
docker compose up --build

# Access application
# Frontend: http://localhost:5173
# Backend: http://localhost:8000
# Database: localhost:5432
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
- **PyPDF2** - PDF generation

### AI
- **Ollama** - Local LLM runtime
- **qwen3:8b** - Language model (configurable)

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
| `OLLAMA_BASE_URL` | Ollama API URL | `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | AI model name | `qwen3:8b` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | `60` |
| `DEBUG` | Debug mode | `True` |
| `ENVIRONMENT` | Environment name | `development` |

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
| GET | `/api/v1/users/me` | Get current user |
| POST | `/api/v1/datasets/` | Upload dataset |
| GET | `/api/v1/datasets/` | List user datasets |
| GET | `/api/v1/datasets/{id}` | Get dataset details |
| DELETE | `/api/v1/datasets/{id}` | Delete dataset |
| GET | `/api/v1/analysis/{dataset_id}` | Get analysis results |
| POST | `/api/v1/chat/sessions/` | Create chat session |
| POST | `/api/v1/chat/sessions/{id}/messages/` | Send message |
| POST | `/api/v1/reports/{dataset_id}/generate/` | Generate PDF report |
| POST | `/api/v1/cleaning/{dataset_id}/preview/` | Preview cleaning |
| POST | `/api/v1/cleaning/{dataset_id}/apply/` | Apply cleaning |

## Testing

### Backend Tests

```bash
cd backend
pytest
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

### Migration Errors

Reset and re-run migrations:

```bash
cd backend
alembic downgrade base
alembic upgrade head
```

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

## Limitations

1. **Dataset Size**: Performance may degrade with files >100MB
2. **AI Availability**: Requires Ollama service; graceful degradation implemented
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
