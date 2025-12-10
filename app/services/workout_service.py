from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from uuid import UUID
import logging
import base64
from app.models.workout_package import WorkoutPackage
from app.models.workout_step import WorkoutStep
from app.services.llm_service import LLMService
from app.services.speech_factory import create_speech_provider
# from app.services.storage import upload_audio_file  # No longer saving to Supabase storage
from app.services.user_config_service import UserConfigService
from mutagen.mp3 import MP3
from io import BytesIO

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
        self.llm_service = LLMService()
    
    def get_workout_package_with_steps(self, package_id: UUID) -> Tuple[WorkoutPackage, List[WorkoutStep]]:
        """
        Get workout package and its steps
        
        Args:
            package_id: Workout package ID
            
        Returns:
            Tuple of (WorkoutPackage, List[WorkoutStep])
            
        Raises:
            ValueError: If package or steps not found
        """
        package = self.db.query(WorkoutPackage).filter(WorkoutPackage.id == package_id).first()
        if not package:
            raise ValueError(f"Workout package {package_id} not found")
        
        if not package.step_ids:
            return package, []
        
        steps = (
            self.db.query(WorkoutStep)
            .filter(WorkoutStep.id.in_(package.step_ids))
            .all()
        )
        
        # Sort steps by the order in step_ids array
        step_dict = {step.id: step for step in steps}
        ordered_steps = [step_dict[step_id] for step_id in package.step_ids if step_id in step_dict]
        
        if len(ordered_steps) != len(package.step_ids):
            missing = set(package.step_ids) - {step.id for step in ordered_steps}
            raise ValueError(f"Some workout steps not found: {missing}")
        
        return package, ordered_steps
    
    def get_tts_settings(self, trainer_config: Dict[str, Any], package: WorkoutPackage) -> Dict[str, Any]:
        """
        Extract TTS settings from trainer_config and package
        
        Args:
            trainer_config: Trainer configuration dict
            package: WorkoutPackage model
            
        Returns:
            Dict with voice_id, voice_provider, language, speaking_rate
        """
        # Fallback chain: trainer_config.voice_id → package.voice_id → default
        voice_id = None
        if trainer_config.get("voice_id"):
            voice_id = str(trainer_config["voice_id"])
        elif package.voice_id:
            voice_id = str(package.voice_id)
        
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
    
    # COMMENTED OUT: Old version that saved to Supabase storage
    # def generate_audio_for_step(
    #     self,
    #     step: WorkoutStep,
    #     user_profile: Dict[str, Any],
    #     trainer_config: Dict[str, Any],
    #     tts_settings: Dict[str, Any]
    # ) -> Dict[str, Any]:
    #     """
    #     Generate personalized audio for a workout step
    #     
    #     Args:
    #         step: WorkoutStep model
    #         user_profile: User profile dict
    #         trainer_config: Trainer config dict
    #         tts_settings: TTS settings dict
    #         
    #     Returns:
    #         Dict with step_id, audio_url, transcript, duration_sec
    #     """
    #     logger.info(f"Starting audio generation for step_id={step.id}, title='{step.title}'")
    #     logger.debug(f"TTS settings: provider={tts_settings.get('voice_provider')}, voice_id={tts_settings.get('voice_id')}")
    #     
    #     # Generate personalized script via LLM
    #     try:
    #         logger.info("Calling Gemini LLM service to generate workout script...")
    #         script = self.llm_service.generate_workout_script(
    #             step_title=step.title,
    #             step_description=step.description,
    #             step_instructions=step.instructions,
    #             step_duration_sec=step.duration_sec,
    #             user_profile=user_profile,
    #             trainer_config=trainer_config
    #         )
    #         logger.info(f"Successfully generated script via Gemini (length={len(script)} chars)")
    #         logger.debug(f"Generated script preview: {script[:100]}...")
    #     except Exception as e:
    #         logger.error(f"Gemini API error: {type(e).__name__}: {str(e)}", exc_info=True)
    #         raise Exception(f"Failed to generate script via Gemini: {str(e)}")
    #     
    #     # Generate TTS audio
    #     try:
    #         logger.info(f"Creating TTS provider: {tts_settings['voice_provider']}")
    #         provider = create_speech_provider(provider_name=tts_settings["voice_provider"])
    #         logger.info(f"Successfully created {tts_settings['voice_provider']} provider")
    #     except Exception as e:
    #         logger.error(f"Failed to create TTS provider: {type(e).__name__}: {str(e)}", exc_info=True)
    #         raise Exception(f"Failed to create TTS provider: {str(e)}")
    #     
    #     # Prepare voice settings for ElevenLabs (if applicable)
    #     voice_settings_kwargs = {}
    #     if tts_settings["voice_provider"] == "elevenlabs":
    #         try:
    #             from elevenlabs import VoiceSettings
    #             # Map speaking_rate (0.5-2.0) to ElevenLabs settings
    #             # ElevenLabs doesn't directly support speaking_rate, but we can adjust style
    #             voice_settings_kwargs["voice_settings"] = VoiceSettings(
    #                 stability=0.5,
    #                 similarity_boost=0.75,
    #                 style=0.0,
    #                 use_speaker_boost=True
    #             )
    #             logger.debug("Configured ElevenLabs VoiceSettings")
    #         except Exception as e:
    #             logger.warning(f"Failed to configure ElevenLabs VoiceSettings: {str(e)}")
    #     
    #     try:
    #         logger.info(f"Calling {tts_settings['voice_provider']} API to generate audio (voice_id={tts_settings.get('voice_id')})...")
    #         audio_data = provider.generate_audio(
    #             text=script,
    #             voice_id=tts_settings["voice_id"],
    #             **voice_settings_kwargs
    #         )
    #         logger.info(f"Successfully generated audio via {tts_settings['voice_provider']} (size={len(audio_data)} bytes)")
    #     except Exception as e:
    #         logger.error(
    #             f"{tts_settings['voice_provider']} API error: {type(e).__name__}: {str(e)}\n"
    #             f"Check if API key is valid and voice_id={tts_settings.get('voice_id')} exists",
    #             exc_info=True
    #         )
    #         raise Exception(f"Failed to generate audio via {tts_settings['voice_provider']}: {str(e)}")
    #     
    #     # Upload to Supabase Storage
    #     try:
    #         logger.info("Uploading audio to Supabase Storage...")
    #         audio_url = upload_audio_file(
    #             audio_data=audio_data,
    #             bucket_name="audio",
    #             content_type="audio/mpeg"
    #         )
    #         logger.info(f"Successfully uploaded audio to: {audio_url}")
    #     except Exception as e:
    #         logger.error(f"Supabase Storage upload error: {type(e).__name__}: {str(e)}", exc_info=True)
    #         raise Exception(f"Failed to upload audio to storage: {str(e)}")
    #     
    #     # Calculate duration
    #     try:
    #         duration_sec = self.calculate_audio_duration(audio_data)
    #         logger.info(f"Calculated audio duration: {duration_sec} seconds")
    #     except Exception as e:
    #         logger.warning(f"Failed to calculate audio duration: {str(e)}")
    #         duration_sec = None
    #     
    #     logger.info(f"Successfully completed audio generation for step_id={step.id}")
    #     return {
    #         "step_id": str(step.id),
    #         "audio_url": audio_url,
    #         "transcript": script,
    #         "duration_sec": duration_sec
    #     }
    
    def generate_audio_for_step(
        self,
        step: WorkoutStep,
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any],
        tts_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate personalized audio for a workout step
        
        Args:
            step: WorkoutStep model
            user_profile: User profile dict
            trainer_config: Trainer config dict
            tts_settings: TTS settings dict
            
        Returns:
            Dict with step_id, audio_blob (base64 encoded), transcript, duration_sec
        """
        logger.info(f"Starting audio generation for step_id={step.id}, title='{step.title}'")
        logger.debug(f"TTS settings: provider={tts_settings.get('voice_provider')}, voice_id={tts_settings.get('voice_id')}")
        
        # Generate personalized script via LLM
        try:
            logger.info("Calling Gemini LLM service to generate workout script...")
            script = self.llm_service.generate_workout_script(
                step_title=step.title,
                step_description=step.description,
                step_instructions=step.instructions,
                step_duration_sec=step.duration_sec,
                user_profile=user_profile,
                trainer_config=trainer_config
            )
            logger.info(f"Successfully generated script via Gemini (length={len(script)} chars)")
            logger.debug(f"Generated script preview: {script[:100]}...")
        except Exception as e:
            logger.error(f"Gemini API error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise Exception(f"Failed to generate script via Gemini: {str(e)}")
        
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
            logger.info(f"Calling {tts_settings['voice_provider']} API to generate audio (voice_id={tts_settings.get('voice_id')})...")
            audio_data = provider.generate_audio(
                text=script,
                voice_id=tts_settings["voice_id"],
                **voice_settings_kwargs
            )
            logger.info(f"Successfully generated audio via {tts_settings['voice_provider']} (size={len(audio_data)} bytes)")
        except Exception as e:
            logger.error(
                f"{tts_settings['voice_provider']} API error: {type(e).__name__}: {str(e)}\n"
                f"Check if API key is valid and voice_id={tts_settings.get('voice_id')} exists",
                exc_info=True
            )
            raise Exception(f"Failed to generate audio via {tts_settings['voice_provider']}: {str(e)}")
        
        # Calculate duration
        try:
            duration_sec = self.calculate_audio_duration(audio_data)
            logger.info(f"Calculated audio duration: {duration_sec} seconds")
        except Exception as e:
            logger.warning(f"Failed to calculate audio duration: {str(e)}")
            duration_sec = None
        
        # Encode audio data as base64 for JSON response
        audio_blob_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        logger.info(f"Successfully completed audio generation for step_id={step.id}")
        return {
            "step_id": str(step.id),
            "audio_blob": audio_blob_base64,
            "transcript": script,
            "duration_sec": duration_sec
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
        
        # Get workout package and steps
        package, steps = self.get_workout_package_with_steps(package_id)
        
        # Get TTS settings
        tts_settings = self.get_tts_settings(trainer_config, package)
        
        # Validate TTS settings
        if tts_settings["voice_provider"] not in ["elevenlabs"]:
            raise ValueError(f"Unsupported voice provider: {tts_settings['voice_provider']}")
        
        speaking_rate = tts_settings.get("speaking_rate", 1.0)
        if not (0.5 <= speaking_rate <= 2.0):
            raise ValueError(f"speaking_rate must be between 0.5 and 2.0, got {speaking_rate}")
        
        # Generate audio for each step
        audio_queue = []
        for step in steps:
            try:
                audio_item = self.generate_audio_for_step(
                    step=step,
                    user_profile=user_profile,
                    trainer_config=trainer_config,
                    tts_settings=tts_settings
                )
                audio_queue.append(audio_item)
            except Exception as e:
                # Log error but continue with other steps
                # In production, you might want to handle this differently
                raise Exception(f"Failed to generate audio for step {step.id}: {str(e)}")
        
        return audio_queue
