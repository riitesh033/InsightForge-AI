# InsightForge AI — Your AI Data Analyst

## Abstract

InsightForge AI is an intelligent web-based dataset analysis platform designed to automate data quality assessment, statistical analysis, and insight generation. Built as a B.Sc. Computer Science final-year project, it combines modern web technologies with AI-powered analytics to help users understand their datasets without requiring deep technical expertise.

## Problem Statement

Organizations and individuals generate vast amounts of data daily, but extracting meaningful insights requires specialized knowledge in statistics, data science, and domain expertise. Many users struggle with:
- Identifying data quality issues (missing values, duplicates, inconsistent types)
- Understanding statistical properties of their datasets
- Detecting outliers and anomalies
- Generating actionable insights from raw data
- Creating professional reports for stakeholders

Existing solutions are either too complex for non-technical users or too simplistic to provide real value.

## Objectives

1. Provide an intuitive interface for uploading and managing datasets (CSV, Excel)
2. Automatically profile datasets and calculate data quality metrics
3. Detect missing values, duplicates, datatype inconsistencies, and outliers
4. Generate comprehensive statistical summaries and correlation analysis
5. Create meaningful visualizations for numerical and categorical data
6. Leverage AI to generate human-readable insights and recommendations
7. Enable natural language chat for dataset exploration
8. Generate professional PDF reports
9. Support safe data cleaning operations with preview functionality
10. Ensure secure multi-user authentication and data isolation

## Existing System Limitations

Traditional data analysis tools require:
- Programming knowledge (Python, R, SQL)
- Statistical expertise
- Manual data quality assessment
- Separate tools for visualization, reporting, and cleaning
- Significant time investment for each analysis

## Proposed System

InsightForge AI provides:
- **Zero-code interface**: Upload data and get instant analysis
- **Automated profiling**: Comprehensive dataset understanding in seconds
- **AI-powered insights**: Natural language explanations of patterns and issues
- **Interactive chat**: Ask questions about your data in plain English
- **One-click reports**: Professional PDF reports ready for sharing
- **Safe cleaning**: Preview changes before applying transformations

## Features

### Authentication & User Management
- Secure user registration and login with JWT tokens
- Protected routes and dataset ownership enforcement
- User profile management

### Dataset Management
- CSV and Excel (.xlsx) file upload with validation
- Dataset listing with search and metadata display
- Dataset deletion with confirmation
- Original and cleaned dataset downloads

### Automated Data Profiling
- Row and column counts
- Memory usage estimation
- Column type detection (numeric, categorical, datetime, boolean)
- Missing value analysis (count, percentage, by column)
- Duplicate row detection
- Datatype inconsistency detection
- Outlier detection using IQR method

### Data Quality Scoring
- Composite score (0-100) based on:
  - Completeness (missing values)
  - Uniqueness (duplicates)
  - Validity (datatype consistency)
  - Consistency (categorical uniformity)

### Statistical Analysis
- Descriptive statistics (mean, median, std dev, min, max, quartiles)
- Correlation matrix for numerical columns
- Distribution analysis

### Visualizations
- Histograms for numerical distributions
- Box plots for outlier visualization
- Bar charts for categorical frequencies
- Correlation heatmaps
- Missing value charts
- Datatype distribution charts

### AI-Powered Features
- **AI Insights**: Automatic generation of findings and recommendations
- **Dataset Chat**: Natural language Q&A about your dataset
- Context-aware responses using dataset profiles

### Data Cleaning
- Remove duplicate rows
- Fill missing values (mean/median/mode)
- Drop rows with missing values
- Normalize categorical values
- Preview changes before application
- Download cleaned datasets

### Report Generation
- Professional PDF reports including:
  - Dataset overview
  - Data quality score
  - Missing value analysis
  - Duplicate analysis
  - Statistical summaries
  - Correlation findings
  - AI insights
  - Cleaning recommendations
- Timestamped generation
- Meaningful filenames

### User Experience
- Responsive design (desktop, tablet, mobile)
- Light/dark theme toggle
- Loading states for all async operations
- Clear error messages and empty states
- Toast notifications for feedback

## Methodology

### Technology Stack

**Frontend:**
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Recharts for visualizations
- Axios for API communication
- React Router for navigation
- Custom hooks for state management

**Backend:**
- FastAPI (Python)
- SQLAlchemy ORM
- PostgreSQL database
- Alembic migrations
- Pandas for data processing
- Ollama integration for AI features
- PyPDF2/ReportLab for PDF generation

**AI Integration:**
- Ollama with qwen3:8b model
- Structured context generation
- Timeout handling and fallbacks

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│    Backend   │────▶│  Database   │
│  (React TS) │◀────│   (FastAPI)  │◀────│ (PostgreSQL)│
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │     AI      │
                    │  (Ollama)   │
                    └─────────────┘
```

### Data Flow

1. **Upload**: User uploads CSV/XLSX → Validation → Storage → Metadata creation
2. **Analysis**: Trigger profiling → Pandas processing → Metrics calculation → AI insights
3. **Chat**: User question → Context retrieval → AI prompt → Response storage
4. **Report**: Report request → Data aggregation → PDF generation → Binary response
5. **Cleaning**: Cleaning selection → Preview → User confirmation → Apply → New version

### Algorithms

**Outlier Detection (IQR Method):**
```
Q1 = 25th percentile
Q3 = 75th percentile
IQR = Q3 - Q1
Lower Bound = Q1 - 1.5 × IQR
Upper Bound = Q3 + 1.5 × IQR
Outliers = values outside [Lower Bound, Upper Bound]
```

**Data Quality Score:**
```
completeness = (1 - missing_percentage / 100) × 25
uniqueness = (1 - duplicate_percentage / 100) × 25
validity = datatype_consistency_score × 25
consistency = categorical_uniformity_score × 25
total = completeness + uniqueness + validity + consistency
```

**Correlation:**
- Pearson correlation coefficient for numerical columns
- Matrix generation for all numerical pairs

## Database Schema

### Users
- id, name, email, password_hash, created_at

### Datasets
- id, user_id, name, original_filename, file_path, row_count, column_count
- file_size, uploaded_at, quality_score, status

### Analyses
- id, dataset_id, profile_data, quality_components, generated_at

### ChatSessions
- id, dataset_id, user_id, title, created_at, updated_at

### ChatMessages
- id, session_id, role, content, created_at

### Reports
- id, dataset_id, report_path, generated_at

## Testing

### Backend Tests
- Authentication endpoints (register, login, token validation)
- Dataset CRUD operations
- File upload validation
- Analysis pipeline
- Chat session management
- Report generation

### Frontend Tests
- Build and TypeScript compilation
- Component rendering
- API integration
- User flows (register → upload → analyze → report)

### Manual QA Checklist
- [ ] Registration and login
- [ ] CSV and XLSX upload
- [ ] Dataset listing and deletion
- [ ] Analysis page with all sections
- [ ] Visualizations rendering
- [ ] AI insights generation
- [ ] Dataset chat functionality
- [ ] PDF report download
- [ ] Data cleaning preview and apply
- [ ] Theme switching
- [ ] Responsive layouts

## Results

The application successfully delivers:
- End-to-end dataset analysis workflow
- Accurate data quality metrics
- Meaningful AI-generated insights
- Professional PDF reports
- Intuitive user interface
- Secure multi-user support

## Limitations

1. **Large Datasets**: Performance may degrade with very large files (>100MB)
2. **AI Availability**: Requires Ollama service for AI features; graceful degradation implemented
3. **Real-time Collaboration**: Single-user per dataset (no concurrent editing)
4. **Advanced Analytics**: Limited to descriptive statistics (no predictive modeling)

## Future Scope

1. **Enhanced AI Models**: Support for multiple LLM providers
2. **Time Series Analysis**: Specialized handling for temporal data
3. **Data Blending**: Join multiple datasets
4. **Custom Transformations**: User-defined cleaning rules
5. **Scheduled Reports**: Automated periodic report generation
6. **Team Collaboration**: Shared workspaces and permissions
7. **API Access**: REST API for programmatic access
8. **Export Formats**: Additional export options (JSON, Parquet)

## Installation

### Prerequisites
- Node.js 18+
- Python 3.10+
- PostgreSQL 14+
- Docker (optional)
- Ollama (for AI features)

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd InsightForge-AI

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Setup database
createdb insightforge
alembic upgrade head

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Setup frontend (new terminal)
cd frontend
npm install
npm run dev

# Access application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Swagger Docs: http://localhost:8000/docs
```

### Docker Deployment

```bash
docker compose up --build
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://user:password@localhost:5432/insightforge
SECRET_KEY=your-secret-key-change-in-production
FRONTEND_URL=http://localhost:5173
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:8b
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DEBUG=True
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000/api/v1
```

## Deployment

### Production Considerations

1. **Security**
   - Change SECRET_KEY to strong random value
   - Use HTTPS/TLS
   - Configure CORS for production domain
   - Enable rate limiting
   - Regular security updates

2. **Database**
   - Use managed PostgreSQL service
   - Enable backups
   - Configure connection pooling

3. **Backend**
   - Use production ASGI server (Gunicorn + Uvicorn workers)
   - Configure logging
   - Set DEBUG=False

4. **Frontend**
   - Build optimized production bundle
   - Serve via CDN or static hosting
   - Configure API base URL

5. **AI Service**
   - Deploy Ollama on separate infrastructure
   - Consider cloud LLM alternatives

## Project Structure

```
InsightForge-AI/
├── frontend/
│   ├── src/
│   │   ├── api/           # API client modules
│   │   ├── components/    # Reusable UI components
│   │   ├── context/       # React contexts
│   │   ├── hooks/         # Custom hooks
│   │   ├── layouts/       # Page layouts
│   │   ├── pages/         # Route pages
│   │   ├── services/      # Business logic services
│   │   ├── types/         # TypeScript types
│   │   ├── utils/         # Utility functions
│   │   └── lib/           # Library configurations
│   ├── package.json
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Core utilities
│   │   ├── crud/          # Database operations
│   │   ├── db/            # Database configuration
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── main.py        # Application entry
│   ├── alembic/           # Database migrations
│   ├── requirements/      # Python dependencies
│   └── Dockerfile
├── docs/                  # Documentation
├── docker-compose.yml
├── README.md
└── .env.example
```

## License

This project is created as an academic submission for B.Sc. Computer Science.

## Contact

For questions or support, please refer to the project documentation or contact the development team.
