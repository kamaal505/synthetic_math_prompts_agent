# Enhanced Synthetic Math Prompts Agent

## New Features Added

### Database Integration
- SQLAlchemy ORM with SQLite
- Batch and Problem models
- Automatic table creation

### New API Endpoints
- `/api/batches/` - Batch management
- `/api/problems/` - Problem management  
- `/api/generation/` - Enhanced generation
- `/api/generation/status/{batch_id}` - Status tracking

### Background Processing
- Asynchronous problem generation
- Real-time status updates
- Database storage during generation

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Set up `.env` file with API keys
3. Run: `uvicorn app.main:app --reload`
4. Access API at `http://localhost:8000`

## Key Changes

- **Database**: Added SQLAlchemy models and services
- **API**: Enhanced with CRUD operations
- **Background Tasks**: Async generation with status tracking
- **Configuration**: Centralized settings management

## Database Schema

**Batch**: id, name, taxonomy_json, pipeline, num_problems, batch_cost, timestamps
**Problem**: id, subject, topic, question, answer, hints, status, batch_id, timestamps, cost, etc.

## API Usage

```bash
# Start generation
POST /api/generation/

# Check status  
GET /api/generation/status/{batch_id}

# List batches
GET /api/batches/

# Get problems
GET /api/problems/?status=valid
```

## Notes

- Core pipeline unchanged
- Cost calculation disabled
- Similarity checks disabled
- All existing functionality preserved 