# Repid Backend

A FastAPI backend for the Repid voice-first personal workout instructor app, featuring Supabase integration, Clerk authentication, and ElevenLabs text-to-speech.

## Features

- **FastAPI** - Modern, fast web framework for building APIs
- **Supabase** - PostgreSQL database and cloud storage
- **Clerk Authentication** - Secure user authentication middleware
- **ElevenLabs TTS** - Text-to-speech audio generation for workout instructions
- **SQLAlchemy ORM** - Database models and relationships
- **Pydantic Schemas** - Data validation and serialization
- **Workout Management** - Complete CRUD operations for workout packages, steps, and voice instructions
- **Audio Storage** - Automatic upload of generated audio files to Supabase Storage
- **Auto-generated Docs** - Interactive API documentation with Swagger UI

## Project Structure

```
repid-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app initialization
│   ├── database.py                # Supabase database configuration
│   ├── middleware/
│   │   └── auth.py                # Clerk authentication middleware
│   ├── models/                    # SQLAlchemy database models
│   │   ├── workout_package.py
│   │   ├── workout_step.py
│   │   └── voice_instruction.py
│   ├── schemas/                   # Pydantic schemas
│   │   └── workout.py
│   ├── routers/                   # API route handlers
│   │   ├── workouts.py
│   │   └── tts.py
│   └── services/                  # Business logic services
│       ├── speech_factory.py
│       ├── speech_provider.py
│       └── storage.py
├── migrations/
│   └── 001_initial_schema.sql     # Database migration script
├── requirements.txt               # Python dependencies
├── setup_venv.sh                 # Virtual environment setup script
└── README.md
```

## Prerequisites

- Python 3.11 or 3.12
- pip
- Supabase account and project
- Clerk account and application
- ElevenLabs API account

## Setup Instructions

### 1. Create Virtual Environment

**Option A: Using the setup script (Recommended)**

```bash
cd repid-backend
chmod +x setup_venv.sh
./setup_venv.sh
source venv/bin/activate
```

**Option B: Manual setup**

```bash
cd repid-backend
python3.11 -m venv venv  # or python3.12
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the `repid-backend/` directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_DB_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# ElevenLabs TTS Configuration
ELEVENLABS_API_KEY=your-elevenlabs-api-key
ELEVENLABS_DEFAULT_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_your-clerk-secret-key

# TTS Provider (default: elevenlabs)
TTS_PROVIDER=elevenlabs
```

**Getting your credentials:**

- **Supabase**: Go to Project Settings > API for URL and keys, Database for connection string
- **Clerk**: Go to your application dashboard > API Keys
- **ElevenLabs**: Navigate to your profile/API section

### 4. Database Setup

1. In your Supabase project, go to the SQL Editor
2. Open `migrations/001_initial_schema.sql`
3. Copy and paste the entire SQL script into the SQL Editor
4. Click "Run" to execute the migration
5. Verify tables were created in the Table Editor

### 5. Storage Buckets Setup

1. Go to Storage in your Supabase dashboard
2. Create two buckets:
   - **audio** - for storing TTS audio files
   - **images** - for storing workout images
3. Set both buckets to **Public** (or configure RLS policies as needed)

### 6. Start the Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Available Endpoints

### Health Check

- `GET /health` - Health check endpoint
- `GET /` - Root endpoint with API info

### Workouts

- `GET /api/v1/workouts` - Get all workout packages
- `GET /api/v1/workouts/{workout_id}` - Get a specific workout package with steps
- `POST /api/v1/workouts` - Create a new workout package (requires authentication)
- `PUT /api/v1/workouts/{workout_id}` - Update a workout package (requires authentication)
- `DELETE /api/v1/workouts/{workout_id}` - Delete a workout package (requires authentication)

### Text-to-Speech

- `POST /api/v1/tts/generate` - Generate TTS audio from text
  - Request body: `{"text": "Your text here", "voice_id": "optional-voice-id"}`
  - Returns: `{"audio_url": "https://..."}`

### Example Requests

**Get All Workouts:**

```bash
curl http://localhost:8000/api/v1/workouts
```

**Get Specific Workout:**

```bash
curl http://localhost:8000/api/v1/workouts/1
```

**Generate TTS Audio:**

```bash
curl -X POST "http://localhost:8000/api/v1/tts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Let'\''s begin with a gentle warm up. Move your arms in circles."
  }'
```

**Create Workout Package (with authentication):**

```bash
curl -X POST "http://localhost:8000/api/v1/workouts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_CLERK_TOKEN" \
  -d '{
    "title": "Morning Stretch",
    "description": "A quick 5-minute morning stretch routine",
    "category": "stretch",
    "estimated_duration_sec": 300
  }'
```

## Database

This project uses **Supabase PostgreSQL** for the database. The connection is configured via the `SUPABASE_DB_URL` environment variable.

### Database Models

- **WorkoutPackage** - Main workout package with title, description, category, and duration
- **WorkoutStep** - Individual steps within a workout package
- **VoiceInstruction** - TTS audio files and transcripts linked to workout steps

## Authentication

The API uses **Clerk** for authentication. Protected endpoints require a valid Clerk JWT token in the `Authorization` header:

```
Authorization: Bearer YOUR_CLERK_TOKEN
```

The authentication middleware (`app/middleware/auth.py`) validates tokens and extracts user information.

## Text-to-Speech

The backend integrates with **ElevenLabs** for generating voice instructions. Generated audio files are automatically uploaded to Supabase Storage and the URL is returned.

### Supported Providers

- **ElevenLabs** (default) - High-quality neural voices

The TTS provider can be configured via the `TTS_PROVIDER` environment variable.

## Development

### Adding New Models

1. Create a new model in `app/models/`:

```python
from sqlalchemy import Column, Integer, String
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
```

2. Create schemas in `app/schemas/`:

```python
from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str

class UserResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True
```

3. Create router in `app/routers/` and include it in `main.py`

4. Update the database schema in Supabase or create a new migration

### Running in Production

For production deployment, use a production-grade server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Or use Gunicorn with Uvicorn workers:

```bash
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Important:** Update CORS origins in `app/main.py` to your production frontend domain.

## Troubleshooting

### Database Connection Error

- Verify `SUPABASE_DB_URL` is correct and password is replaced
- Check that the database is accessible from your network
- Ensure the migration has been run in Supabase

### TTS Generation Fails

- Check `ELEVENLABS_API_KEY` is valid and has sufficient credits
- Verify the voice ID exists in your ElevenLabs account
- Check network connectivity to ElevenLabs API

### Storage Upload Fails

- Verify Supabase Storage buckets exist (`audio` and `images`)
- Check bucket permissions are set correctly
- Ensure `SUPABASE_SERVICE_KEY` has storage access

### Authentication Issues

- Verify `CLERK_SECRET_KEY` is correct
- Check token format in Authorization header
- Ensure Clerk application is properly configured

## Learn More

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Clerk Documentation](https://clerk.com/docs)
- [ElevenLabs API Documentation](https://elevenlabs.io/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
