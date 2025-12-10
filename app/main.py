from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import workouts, tts, users, workout_sessions, workout_audio, user_config
from app.database import engine, Base
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Repid API",
    description="Voice-first personal workout instructor API",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        error_msg = str(e)
        if "could not translate host name" in error_msg.lower() or "nodename nor servname" in error_msg.lower():
            logger.error(
                f"Database connection failed - DNS resolution error\n"
                f"Error: {error_msg}\n"
                "\nThis usually means:\n"
                "  1. The Supabase project reference ID in SUPABASE_DB_URL is incorrect\n"
                "  2. The Supabase project has been deleted or paused\n"
                "  3. Network/DNS issues\n"
                "\nTo fix this:\n"
                "  1. Go to Supabase Dashboard > Your Project > Settings > Database\n"
                "  2. Under 'Connection string', select 'URI' (not 'Connection pooling')\n"
                "  3. Copy the connection string and replace [YOUR-PASSWORD] with your actual password\n"
                "  4. Verify the project reference ID matches your project URL\n"
                "     (Your project URL: https://[PROJECT-REF].supabase.co)\n"
                "     (DB hostname should be: db.[PROJECT-REF].supabase.co)"
            )
        else:
            logger.warning(
                f"Could not create database tables: {error_msg}. "
                "The app will continue, but database operations may fail."
            )

# CORS middleware - configured for Expo app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific Expo app origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workouts.router, prefix="/api/v1", tags=["workouts"])
app.include_router(tts.router, prefix="/api/v1", tags=["tts"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(workout_sessions.router, prefix="/api/v1", tags=["workout-sessions"])
app.include_router(workout_audio.router, prefix="/api/v1", tags=["workout-audio"])
app.include_router(user_config.router, prefix="/api/v1", tags=["user-config"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Repid API",
        "docs": "/docs",
        "health": "/health",
    }

