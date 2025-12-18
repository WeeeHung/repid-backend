from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from uuid import UUID
import logging
import base64
from app.models.workout_package import WorkoutPackage
from app.models.workout_step import WorkoutStep
from app.services.llm_factory import create_llm_provider
from app.services.speech_factory import create_speech_provider
# from app.services.storage import upload_audio_file  # No longer saving to Supabase storage
from app.services.user_config_service import UserConfigService
from app.types import TimelineItem
from mutagen.mp3 import MP3
from io import BytesIO
from pydub import AudioSegment
from pydub.silence import split_on_silence

logger = logging.getLogger(__name__)


class WorkoutService:
    """Service for workout-related business logic"""
    
    def __init__(self, db: Session):
        """
        Initialize workout service
        
        Args:
            db: Database session
        """
        self.db = db
        self.llm_service = create_llm_provider()
    
    def get_workout_package_with_steps(self, package_id: UUID) -> Tuple[WorkoutPackage, List[TimelineItem]]:
        """
        Get workout package and its timeline items (merged steps with overrides and sets)
        
        Args:
            package_id: Workout package ID
            
        Returns:
            Tuple of (WorkoutPackage, List[TimelineItem])
            TimelineItem includes all WorkoutStep fields plus sets and override fields from timeline
            
        Raises:
            ValueError: If package or steps not found
        """
        # THIS DB QUERIES SHOULD BE CACHED in redis or something
        package = self.db.query(WorkoutPackage).filter(WorkoutPackage.id == package_id).first()
        if not package:
            raise ValueError(f"Workout package {package_id} not found")
        
        if not package.timeline:
            return package, []

        # Extract IDs from timeline list
        step_ids_list = []
        for item in package.timeline:
            if isinstance(item, dict):
                # Handle dict with overrides
                s_id = item.get("id") or item.get("step_id")
                if s_id:
                    step_ids_list.append(s_id)
            else:
                # Handle plain ID
                step_ids_list.append(item)
        
        steps = (
            self.db.query(WorkoutStep)
            .filter(WorkoutStep.id.in_(step_ids_list))
            .all()
        )
        
        # Create a dict for quick lookup
        step_dict = {str(step.id): step for step in steps}
        timeline_items: List[TimelineItem] = []
        
        # Build TimelineItems by merging step data with timeline overrides
        for item in package.timeline:
            step_id = None
            overrides: Dict[str, Any] = {}
            
            if isinstance(item, dict):
                step_id = item.get("id") or item.get("step_id")
                overrides = item.copy()
            else:
                step_id = item
            
            if not step_id:
                continue
                
            step_id_str = str(step_id)
            if step_id_str not in step_dict:
                raise ValueError(f"Workout step {step_id} not found in database")
            
            original_step = step_dict[step_id_str]
            
            # Build TimelineItem starting with all step fields
            timeline_item: TimelineItem = {
                "id": step_id_str,
                "step_id": step_id_str,
                "title": original_step.title,
                "description": original_step.description,
                "category": original_step.category,
                "media_url": original_step.media_url,
                "instructions": original_step.instructions,
                "exercise_type": original_step.exercise_type,
                "estimated_duration_sec": original_step.estimated_duration_sec,
                "default_reps": original_step.default_reps,
                "default_duration_sec": original_step.default_duration_sec,
                "default_weight_kg": original_step.default_weight_kg,
                "default_distance_m": original_step.default_distance_m,
            }
            
            # Apply overrides from timeline (excluding id/step_id which we already set)
            for key, value in overrides.items():
                if key in ["id", "step_id"]:
                    continue
                
                # Handle sets specially - it should be a list of dicts
                if key == "sets" and value is not None:
                    if isinstance(value, list):
                        timeline_item["sets"] = value
                    else:
                        timeline_item["sets"] = None
                else:
                    # Apply other overrides (sets, rest_between_sets_s, reps, weight_kg, etc.)
                    timeline_item[key] = value
            
            timeline_items.append(timeline_item)
        
        if len(timeline_items) != len(step_ids_list):
            missing = set(map(str, step_ids_list)) - {item["id"] for item in timeline_items}
            raise ValueError(f"Some workout steps not found: {missing}")
        
        return package, timeline_items

    # DEPRECATED: use generate_audio_for_voice_event instead.
    
    def get_tts_settings(self, trainer_config: Dict[str, Any], package: WorkoutPackage) -> Dict[str, Any]:
        """
        Extract TTS settings from trainer_config and package
        
        Args:
            trainer_config: Trainer configuration dict
            package: WorkoutPackage model
            
        Returns:
            Dict with voice_id, voice_provider, language, speaking_rate
        """
        # Fallback chain: trainer_config.voice_id → default
        voice_id = None
        if trainer_config.get("voice_id"):
            voice_id = str(trainer_config["voice_id"])
        
        return {
            "voice_id": voice_id,
            "voice_provider": trainer_config.get("voice_provider", "elevenlabs"),
            "language": trainer_config.get("language", "en"),
            "speaking_rate": trainer_config.get("speaking_rate", 1.0)
        }
    
    def calculate_audio_duration(self, audio_data: bytes) -> Optional[int]:
        """
        Calculate audio duration in seconds
        
        Args:
            audio_data: Audio file bytes
            
        Returns:
            Duration in seconds or None if calculation fails
        """
        try:
            audio_file = BytesIO(audio_data)
            audio = MP3(audio_file)
            return int(audio.info.length)
        except Exception:
            return None

    def split_cue_audio(self, cue_audio_data: bytes) -> List[str]:
        """
        Split cue audio into multiple segments based on silence detection.
        
        Splits the audio when there is approximately 1 second of silence.
        Returns base64-encoded audio segments.
        
        Args:
            cue_audio_data: Audio file bytes (typically MP3)
            
        Returns:
            List of base64-encoded audio segments
        """
        try:
            # Load audio from bytes
            audio_file = BytesIO(cue_audio_data)
            audio_segment = AudioSegment.from_mp3(audio_file)

            # Split on silence:
            # - min_silence_len: minimum length of silence to split on (1000ms = 1 second)
            # - silence_thresh: silence threshold in dBFS (default is -16, lower = more sensitive)
            # - keep_silence: keep some silence at the beginning/end of chunks (500ms)
            chunks = split_on_silence(
                audio_segment,
                min_silence_len=1000,  # 1 second of silence
                silence_thresh=-40,    # dBFS threshold (adjust if needed)
                keep_silence=500       # Keep 500ms of silence at chunk boundaries
            )
            
            # If no silence detected or splitting failed, return the original audio
            if not chunks or len(chunks) == 0:
                logger.debug("No silence detected, returning full audio as single segment")
                return [base64.b64encode(cue_audio_data).decode("utf-8")]
            
            # Encode each chunk as base64
            audio_blobs = []
            for i, chunk in enumerate(chunks):
                # Export chunk to bytes
                chunk_buffer = BytesIO()
                chunk.export(chunk_buffer, format="mp3")
                chunk_bytes = chunk_buffer.getvalue()
                
                # Encode as base64
                audio_blobs.append(base64.b64encode(chunk_bytes).decode("utf-8"))
                logger.debug(
                    f"Created audio segment {i+1}/{len(chunks)} "
                    f"(duration: {len(chunk)}ms, size: {len(chunk_bytes)} bytes)"
                )
            
            logger.info(f"Split cue audio into {len(audio_blobs)} segments based on silence detection")
            return audio_blobs
            
        except Exception as e:
            logger.error(f"Error splitting cue audio: {type(e).__name__}: {str(e)}", exc_info=True)
            # Fallback: return original audio as single segment
            try:
                return [base64.b64encode(cue_audio_data).decode("utf-8")]
            except Exception:
                return []
    
    def generate_audio_for_voice_event(
        self,
        order: int,
        intro_text: str,
        start_text: str,
        cue_text: str,
        tts_settings: Dict[str, Any],
        exercise_type: str = "duration"
    ) -> Dict[str, Any]:
        """
        Generate TTS audio for a single voice event.

        This produces:
        - One intro audio blob
        - One start audio blob
        - Cue audio blobs (only for duration exercises)
        """
        logger.info(f"Starting audio generation for voice_event order={order}")
        logger.debug(
            "TTS settings: provider=%s, voice_id=%s",
            tts_settings.get("voice_provider"),
            tts_settings.get("voice_id"),
        )

        # Generate TTS audio
        try:
            logger.info(f"Creating TTS provider: {tts_settings['voice_provider']}")
            provider = create_speech_provider(provider_name=tts_settings["voice_provider"])
            logger.info(f"Successfully created {tts_settings['voice_provider']} provider")
        except Exception as e:
            logger.error(f"Failed to create TTS provider: {type(e).__name__}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create TTS provider: {str(e)}")

        # Prepare voice settings for ElevenLabs (if applicable)
        voice_settings_kwargs = {}
        if tts_settings["voice_provider"] == "elevenlabs":
            try:
                from elevenlabs import VoiceSettings
                # Map speaking_rate (0.5-2.0) to ElevenLabs settings
                # ElevenLabs doesn't directly support speaking_rate, but we can adjust style
                voice_settings_kwargs["voice_settings"] = VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
                logger.debug("Configured ElevenLabs VoiceSettings")
            except Exception as e:
                logger.warning(f"Failed to configure ElevenLabs VoiceSettings: {str(e)}")

        try:
            # Intro audio
            logger.info(
                "Calling %s API to generate INTRO audio (voice_id=%s)...",
                tts_settings["voice_provider"],
                tts_settings.get("voice_id"),
            )
            intro_audio_data = provider.generate_audio(
                text=intro_text,
                voice_id=tts_settings["voice_id"],
                **voice_settings_kwargs
            )
            logger.info(
                "Successfully generated INTRO audio via %s (size=%s bytes)",
                tts_settings["voice_provider"],
                len(intro_audio_data),
            )

            # Start audio
            logger.info(
                "Calling %s API to generate START audio (voice_id=%s)...",
                tts_settings["voice_provider"],
                tts_settings.get("voice_id"),
            )
            start_audio_data = provider.generate_audio(
                text=start_text,
                voice_id=tts_settings["voice_id"],
                **voice_settings_kwargs
            )
            logger.info(
                "Successfully generated START audio via %s (size=%s bytes)",
                tts_settings["voice_provider"],
                len(start_audio_data),
            )

            # Cue audio (only for duration exercises)
            cue_audio_data = None
            if exercise_type == "duration":
                logger.info(
                    "Calling %s API to generate CUE audio (voice_id=%s)...",
                    tts_settings["voice_provider"],
                    tts_settings.get("voice_id"),
                )
                cue_audio_data = provider.generate_audio(
                    text=cue_text,
                    voice_id=tts_settings["voice_id"],
                    **voice_settings_kwargs
                )
                logger.info(
                    "Successfully generated CUE audio via %s (size=%s bytes)",
                    tts_settings["voice_provider"],
                    len(cue_audio_data),
                )
            else:
                logger.info("Skipping CUE audio generation for non-duration exercise (type=%s)", exercise_type)
        except Exception as e:
            logger.error(
                f"{tts_settings['voice_provider']} API error: {type(e).__name__}: {str(e)}\n"
                f"Check if API key is valid and voice_id={tts_settings.get('voice_id')} exists",
                exc_info=True
            )
            raise Exception(f"Failed to generate audio via {tts_settings['voice_provider']}: {str(e)}")

        # Encode audio data as base64 for JSON response
        intro_audio_blob_base64 = base64.b64encode(intro_audio_data).decode("utf-8")
        start_audio_blob_base64 = base64.b64encode(start_audio_data).decode("utf-8")

        # Split cue audio into segments (only for duration exercises)
        if cue_audio_data:
            cue_audio_blobs = self.split_cue_audio(cue_audio_data)
        else:
            cue_audio_blobs = []

        logger.info(f"Successfully completed audio generation for voice_event order={order}")
        return {
            "order": order,
            "intro_audio_blob": intro_audio_blob_base64,
            "start_audio_blob": start_audio_blob_base64,
            "cue_audio_blobs": cue_audio_blobs,
        }
    
    def generate_audio_package(
        self,
        package_id: UUID,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Generate complete audio package for a workout
        
        Args:
            package_id: Workout package ID
            user_id: User ID
            
        Returns:
            List of audio queue items
        """
        # Get user configuration
        user_config = UserConfigService.get_all_user_config(self.db, user_id)
        user_profile = user_config["profile"] or {}
        trainer_config = user_config["trainer_config"]
        
        # Get workout package and timeline items (merged steps with sets and overrides)
        package, timeline_items = self.get_workout_package_with_steps(package_id)
        
        # Get TTS settings
        tts_settings = self.get_tts_settings(trainer_config, package)
        
        # Validate TTS settings
        if tts_settings["voice_provider"] not in ["elevenlabs"]:
            raise ValueError(f"Unsupported voice provider: {tts_settings['voice_provider']}")
        
        speaking_rate = tts_settings.get("speaking_rate", 1.0)
        if not (0.5 <= speaking_rate <= 2.0):
            raise ValueError(f"speaking_rate must be between 0.5 and 2.0, got {speaking_rate}")
        
        # Generate audio for each timeline item as a simple ordered voice event.
        # NOTE: This is an initial implementation. In the future, we should:
        # - Build a richer VoiceEvent from the workout timeline (including reps, phase_type, etc.)
        # - Ask the LLM to produce an intro plus cues[] (rep_count * 2) per event.
        # - Use sets information to generate per-set cues
        audio_queue = []
        for index, timeline_item in enumerate(timeline_items):
            order = index + 1

            # Generate a base script via LLM (reusing the existing method).
            try:
                logger.info("Calling LLM service to generate workout script for order=%s...", order)
                script_parts = self.llm_service.generate_workout_script(
                    timeline_item=timeline_item,
                    user_profile=user_profile,
                    trainer_config=trainer_config,
                )
                intro_text = script_parts.get("intro_text") or ""
                start_text = script_parts.get("start_text") or ""
                cue_text = script_parts.get("cue_text") or ""

                logger.info(
                    "Successfully generated script via LLM (order=%s, intro_len=%s, start_len=%s, cue_len=%s)",
                    order,
                    len(intro_text),
                    len(start_text),
                    len(cue_text),
                )
                logger.debug(
                    "Generated intro preview (order=%s): %s...",
                    order,
                    intro_text[:100],
                )
            except Exception as e:
                logger.error(
                    "LLM error while generating script for order=%s: %s: %s",
                    order,
                    type(e).__name__,
                    str(e),
                    exc_info=True,
                )
                raise Exception(f"Failed to generate script via LLM for order={order}: {str(e)}")

            try:
                exercise_type = timeline_item.get("exercise_type", "duration")
                audio_item = self.generate_audio_for_voice_event(
                    order=order,
                    intro_text=intro_text,
                    start_text=start_text,
                    cue_text=cue_text,
                    tts_settings=tts_settings,
                    exercise_type=exercise_type,
                )
                audio_queue.append(audio_item)
            except Exception as e:
                raise Exception(f"Failed to generate audio for voice_event order={order}: {str(e)}")

        return audio_queue

