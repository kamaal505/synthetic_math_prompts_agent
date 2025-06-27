# Synthetic Math Prompts Agent - Enhanced FastAPI System

A comprehensive FastAPI-based system for generating, validating, and managing synthetic math problems using a multi-stage AI pipeline.

## Features

- **Multi-stage AI Pipeline**: Generator, Hinter, Checker, Target, and Judge agents
- **RESTful API**: Complete CRUD operations for batches and problems
- **Database Integration**: SQLite database with SQLAlchemy ORM
- **Background Processing**: Asynchronous problem generation
- **Real-time Status Tracking**: Monitor generation progress
- **Comprehensive Filtering**: Filter problems by batch, status, and more
- **Cost Tracking**: Track generation costs (optional)
- **Similarity Detection**: Prevent duplicate problems (optional)

## Architecture

```
synthetic_math_prompts_agent/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── batches.py         # Batch management
│   │   ├── problems.py        # Problem management
│   │   ├── generation.py      # Generation endpoints
│   │   └── routes.py          # Main router
│   ├── models/                # Database models
│   │   ├── database.py        # Database configuration
│   │   ├── models.py          # SQLAlchemy models
│   │   └── schemas.py         # Pydantic schemas
│   ├── services/              # Business logic
│   │   ├── batch_service.py   # Batch operations
│   │   ├── problem_service.py # Problem operations
│   │   └── pipeline_service.py # Enhanced pipeline
│   ├── config.py              # Configuration
│   └── main.py                # FastAPI app
├── core/                      # Core pipeline (unchanged)
├── database/                  # Database files
└── requirements.txt           # Dependencies
```

## Installation

1. **Clone and setup virtual environment**:
```bash
cd synthetic_math_prompts_agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**:
Create a `.env` file in the root directory:
```env
OPENAI_KEY=your_openai_api_key
GEMINI_KEY=your_gemini_api_key
DEEPSEEK_KEY=your_deepseek_api_key
DATABASE_URL=sqlite:///./database/math_agent.db
```

4. **Run the application**:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Core Generation
- `POST /api/generate` - Generate problems (original endpoint)
- `POST /api/generation/` - Start generation with database storage
- `GET /api/generation/status/{batch_id}` - Get generation status

### Batch Management
- `GET /api/batches/` - List all batches with statistics
- `GET /api/batches/{batch_id}` - Get specific batch
- `DELETE /api/batches/{batch_id}` - Delete batch

### Problem Management
- `GET /api/problems/` - List all problems (with filters)
- `GET /api/problems/problem/{problem_id}` - Get specific problem
- `GET /api/problems/batch/{batch_id}/problems` - Get problems by batch

### Utility
- `GET /` - Root endpoint
- `GET /health` - Health check

## Usage Examples

### 1. Start Problem Generation

```bash
curl -X POST "http://localhost:8000/api/generation/" \
  -H "Content-Type: application/json" \
  -d '{
    "num_problems": 5,
    "engineer_model": {
      "provider": "gemini",
      "model_name": "gemini-2.5-pro"
    },
    "checker_model": {
      "provider": "openai",
      "model_name": "o3-mini"
    },
    "target_model": {
      "provider": "openai",
      "model_name": "o1"
    },
    "taxonomy": {
      "Algebra": ["Linear Equations", "Quadratic Functions"],
      "Calculus": ["Derivatives", "Integration"]
    }
  }'
```

### 2. Check Generation Status

```bash
curl "http://localhost:8000/api/generation/status/1"
```

### 3. List All Batches

```bash
curl "http://localhost:8000/api/batches/"
```

### 4. Get Problems by Status

```bash
curl "http://localhost:8000/api/problems/?status=valid"
```

### 5. Get Problems from Specific Batch

```bash
curl "http://localhost:8000/api/problems/batch/1/problems"
```

## Database Schema

### Batch Table
- `id`: Primary key
- `name`: Batch name
- `taxonomy_json`: JSON taxonomy configuration
- `pipeline`: JSON pipeline configuration
- `num_problems`: Target number of valid problems
- `batch_cost`: Total cost for the batch
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Problem Table
- `id`: Primary key
- `subject`: Math subject
- `topic`: Specific topic
- `question`: Problem text
- `answer`: Solution
- `hints`: JSON hints object
- `rejection_reason`: Reason if discarded
- `status`: 'discarded', 'solved', or 'valid'
- `batch_id`: Foreign key to batch
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `problem_embedding`: Vector embedding (optional)
- `similar_problems`: Similar problems data (optional)
- `cost`: Individual problem cost
- `target_model_answer`: Target model's answer
- `hints_were_corrected`: Whether hints were corrected

## Configuration

The system uses a centralized configuration in `app/config.py`:

- **API Keys**: OpenAI, Gemini, DeepSeek
- **Database**: SQLite by default, configurable via DATABASE_URL
- **Similarity**: Threshold and embedding model settings
- **App Settings**: Name, version, etc.

## Development

### Adding New Endpoints

1. Create new router in `app/api/`
2. Add business logic in `app/services/`
3. Include router in `app/api/routes.py`

### Database Migrations

The system uses SQLAlchemy with automatic table creation. For production, consider using Alembic for migrations.

### Testing

Test the API using tools like Postman, curl, or the built-in FastAPI docs at `http://localhost:8000/docs`.

## Notes

- **Cost Calculation**: Disabled as requested
- **Similarity Checks**: Disabled as requested
- **Core Pipeline**: Unchanged - all existing functionality preserved
- **Database**: SQLite for simplicity, easily changeable to PostgreSQL/MySQL

## Troubleshooting

1. **Import Errors**: Ensure virtual environment is activated
2. **Database Errors**: Check database file permissions
3. **API Key Errors**: Verify .env file configuration
4. **Pipeline Errors**: Check core pipeline dependencies

## License

This project maintains the same license as the original synthetic math prompts agent.
