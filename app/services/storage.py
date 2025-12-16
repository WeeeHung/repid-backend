import os
from typing import Optional
from supabase import create_client, Client
from pydantic_settings import BaseSettings
import uuid
from datetime import datetime


class StorageSettings(BaseSettings):
    """Settings for Supabase Storage"""
    supabase_url: str
    supabase_secret_key: str  # Uses SUPABASE_SECRET_KEY (deprecated: SUPABASE_SERVICE_KEY)
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    settings = StorageSettings()
    return create_client(settings.supabase_url, settings.supabase_secret_key)


def upload_audio_file(
    audio_data: bytes,
    bucket_name: str = "audio",
    file_name: Optional[str] = None,
    content_type: str = "audio/mpeg"
) -> str:
    """
    Upload audio file to Supabase Storage
    
    Args:
        audio_data: Audio file bytes
        bucket_name: Storage bucket name (default: "audio")
        file_name: Optional custom file name (generates UUID if not provided)
        content_type: MIME type (default: "audio/mpeg" for MP3)
        
    Returns:
        str: Public URL of uploaded file
    """
    client = get_supabase_client()
    
    # Generate file name if not provided
    if not file_name:
        file_name = f"{uuid.uuid4()}.mp3"
    
    # Ensure file has .mp3 extension if not present
    if not file_name.endswith(('.mp3', '.wav', '.m4a')):
        file_name = f"{file_name}.mp3"
    
    # Upload file
    response = client.storage.from_(bucket_name).upload(
        path=file_name,
        file=audio_data,
        file_options={
            "content-type": content_type,
            "upsert": False
        }
    )
    
    # Get public URL
    public_url = client.storage.from_(bucket_name).get_public_url(file_name)
    
    return public_url


def upload_image_file(
    image_data: bytes,
    bucket_name: str = "images",
    file_name: Optional[str] = None,
    content_type: str = "image/png"
) -> str:
    """
    Upload image file to Supabase Storage
    
    Args:
        image_data: Image file bytes
        bucket_name: Storage bucket name (default: "images")
        file_name: Optional custom file name (generates UUID if not provided)
        content_type: MIME type (default: "image/png")
        
    Returns:
        str: Public URL of uploaded file
    """
    client = get_supabase_client()
    
    # Generate file name if not provided
    if not file_name:
        # Determine extension from content type
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/webp": ".webp"
        }
        ext = ext_map.get(content_type, ".png")
        file_name = f"{uuid.uuid4()}{ext}"
    
    # Upload file
    response = client.storage.from_(bucket_name).upload(
        path=file_name,
        file=image_data,
        file_options={
            "content-type": content_type,
            "upsert": False
        }
    )
    
    # Get public URL
    public_url = client.storage.from_(bucket_name).get_public_url(file_name)
    
    return public_url


def delete_file(bucket_name: str, file_path: str) -> bool:
    """
    Delete a file from Supabase Storage
    
    Args:
        bucket_name: Storage bucket name
        file_path: Path to file in bucket
        
    Returns:
        bool: True if successful
    """
    try:
        client = get_supabase_client()
        client.storage.from_(bucket_name).remove([file_path])
        return True
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False

