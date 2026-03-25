# SwasthyaAI Regulator - Quick Start Guide

Get the application running in 5 minutes!

## Option 1: Quick Start (Recommended for Development)

### Prerequisites
- Python 3.9+
- PostgreSQL (installed and running)
- Git

### Steps

1. **Clone and Setup**
```bash
cd "c:\Users\email\OneDrive\Desktop\SwasthyaAI Regulator"
python -m venv venv
venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Environment**
```bash
copy .env.example .env
# Edit .env with your database credentials
```

4. **Initialize Database**
```bash
python init_db.py
```

5. **Run the Server**
```bash
python -m flask run
```

Access the API at: **http://localhost:5000**

Test health: **http://localhost:5000/api/health**

## Option 2: Docker Setup (Recommended for Production)

### Prerequisites
- Docker
- Docker Compose

### Steps

1. **Configure Environment**
```bash
copy .env.example .env
# Edit .env with desired database credentials
```

2. **Start All Services**
```bash
docker-compose up -d
```

This starts:
- Backend API (port 5000)
- PostgreSQL Database (port 5432)
- Redis Cache (port 6379)
- Celery Worker (background processing)
- Flower Monitoring (port 5555)

3. **Check Status**
```bash
docker-compose ps
docker-compose logs backend
```

4. **Stop Services**
```bash
docker-compose down
```

## First API Requests

### 1. Get Authentication Token
```bash
curl -X POST http://localhost:5000/api/auth/token
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Check Health
```bash
curl http://localhost:5000/api/health
```

### 3. Upload Document
```bash
# Save the token from step 1
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."

curl -X POST http://localhost:5000/api/submissions/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "type=form_44"
```

Response:
```json
{
  "submission_id": "550e8400-e29b-41d4-a71....",
  "status": "processing",
  "message": "Document uploaded successfully"
}
```

### 4. Process Document
```bash
SUBMISSION_ID="550e8400-e29b-41d4-a71...."

curl -X POST http://localhost:5000/api/submissions/$SUBMISSION_ID/process \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Get Results
```bash
curl http://localhost:5000/api/submissions/$SUBMISSION_ID/results \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "submission_id": "550e8400-e29b-41d4-a71...",
  "status": "completed",
  "anonymized_data": {
    "anonymized_text": "Patient PERSON_001 was treated with...",
    "pii_stats": {
      "phone": 2,
      "email": 1,
      "aadhar": 1,
      "pan": 1
    },
    "k_anonymity": 5.2
  },
  "summary": {
    "abstract": "Clinical trial for drug X shows...",
    "key_findings": ["92% efficacy", "Mild side effects"],
    "compression_ratio": 0.15
  },
  "compliance": {
    "is_compliant": true,
    "score": 87.5,
    "frameworks": {
      "dpdp": true,
      "ndhm": true,
      "icmr": true,
      "cdsco": true
    }
  }
}
```

## Project Files Overview

### Core Backend
- `backend/app.py` - Flask application with all API routes
- `backend/config.py` - Environment configuration
- `backend/models.py` - Database schema (7 models)
- `backend/modules/` - AI processing engines

### AI Modules
- `ocr_engine.py` - Text extraction from PDFs/images
- `anonymizer.py` - DPDP-compliant PII removal
- `summarizer.py` - BART-based text summarization
- `compliance_validator.py` - Multi-framework compliance checking

### DevOps
- `Dockerfile` - Production Docker image
- `docker-compose.yml` - Local development environment
- `init_db.py` - Database initialization script
- `requirements.txt` - Python dependencies

### Tests & Documentation
- `tests/test_basic.py` - Unit tests
- `README.md` - Complete documentation
- `.env.example` - Environment template
- `QUICKSTART.md` - This file

## Common Commands

### Database Operations
```bash
# Initialize database
python init_db.py

# Reset database (WARNING: Deletes data)
python -c "from backend.app import create_app; from backend.models import db; app = create_app(); db.drop_all(); db.create_all()"

# Connect to database
psql -U swastya_user -d swastya_regulator -h localhost
```

### Running Tests
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=backend

# Specific test
pytest tests/test_basic.py::TestOCREngine -v
```

### Docker Commands
```bash
# View logs
docker-compose logs -f backend

# Run command in container
docker-compose exec backend python init_db.py

# Rebuild containers
docker-compose build --no-cache

# Access database in container
docker-compose exec postgres psql -U swastya_user -d swastya_regulator
```

## Troubleshooting

### "Database connection refused"
- Ensure PostgreSQL is running: `psql --version`
- Check DATABASE_URL in .env
- Verify PostgreSQL credentials

### "Tesseract not found"
```bash
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# Linux: apt-get install tesseract-ocr
# macOS: brew install tesseract
```

### "Module not found" errors
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Container issues
```bash
# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose down && docker-compose up -d --build
```

### Port already in use
```bash
# Change ports in docker-compose.yml or:
docker-compose down
```

## Development Workflow

1. **Make code changes** in `backend/` folder
2. **Test locally** with `pytest`
3. **Run Flask server** with `python -m flask run`
4. **Verify API** with curl commands
5. **Check logs** with `flask --debug run` for verbose output

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| FLASK_ENV | development | Environment (development/testing/production) |
| DATABASE_URL | postgresql://... | PostgreSQL connection string |
| JWT_SECRET_KEY | dev-secret-key | JWT signing key (CHANGE IN PRODUCTION) |
| UPLOAD_FOLDER | ./uploads | Where to store uploaded files |
| DATA_RETENTION_DAYS | 90 | Days to keep data before deletion |
| K_ANONYMITY_THRESHOLD | 5 | Minimum k-anonymity score |
| SUMMARIZATION_MODEL | facebook/bart-large-cnn | Hugging Face model for summarization |

## Next Steps

1. ✅ **Backend running** - Test with API calls
2. 📋 **Build frontend** - React components for upload/results
3. 🚀 **Deploy** - Push to Railway.app (backend) and Vercel (frontend)
4. 📊 **Monitor** - Use Flower for Celery task monitoring
5. 🧪 **Test** - Run full test suite before production

## Getting Help

- Check `README.md` for full documentation
- Review `init_db.py` for setup details
- Check logs: `docker-compose logs backend`
- Review test files: `tests/test_basic.py`

## Performance Notes

- First BART summarization download is ~1.6GB (cached after)
- Average document processing: 20-30 seconds
- Database queries are indexed for compliance lookups
- Redis caching enabled for repeated requests

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2024  
**Hackathon Timeline**: 45 days
