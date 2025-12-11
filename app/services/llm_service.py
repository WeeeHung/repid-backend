import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
import google.generativeai as genai


class LLMSettings(BaseSettings):
    """Settings for LLM service configuration"""
    gemini_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"


class LLMService:
    """Service for generating personalized workout scripts using Gemini"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM service
        
        Args:
            api_key: Gemini API key (defaults to env variable)
        """
        settings = LLMSettings()
        self.api_key = api_key or settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for LLM service")
        
        genai.configure(api_key=self.api_key)
        self.model_name = 'gemini-2.5-flash'
        self.model = genai.GenerativeModel(self.model_name)
    
    def generate_workout_script(
        self,
        step_title: str,
        step_description: Optional[str],
        step_instructions: Optional[str],
        step_duration_sec: Optional[int],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """
        Generate personalized workout script for a step
        
        Args:
            step_title: Title of the workout step
            step_description: Description of the step
            step_instructions: Base instructions for the step
            step_duration_sec: Duration of the step in seconds
            user_profile: User profile data (height_cm, weight_kg, sex, fitness_level, goal)
            trainer_config: Trainer config (persona_style, enthusiasm_cat, age_cat, gender)
            
        Returns:
            str: Personalized script text
        """
        # Extract persona settings
        persona_style = trainer_config.get("persona_style", "standard")
        enthusiasm_cat = trainer_config.get("enthusiasm_cat", 3)
        age_cat = trainer_config.get("age_cat", 3)
        gender = trainer_config.get("gender") or user_profile.get("sex")
        
        # Map enthusiasm to descriptive words
        enthusiasm_map = {
            1: "very calm and gentle",
            2: "calm and encouraging",
            3: "motivating and energetic",
            4: "highly energetic and enthusiastic",
            5: "extremely intense and passionate"
        }
        enthusiasm_desc = enthusiasm_map.get(enthusiasm_cat, "motivating and energetic")
        
        # Map persona style to tone
        persona_map = {
            "chill": "relaxed, friendly, and laid-back",
            "standard": "professional, clear, and supportive",
            "locked-in": "intense, focused, and driven"
        }
        persona_desc = persona_map.get(persona_style, "professional, clear, and supportive")
        
        # Build user context
        fitness_level = user_profile.get("fitness_level", "intermediate")
        goal = user_profile.get("goal", "general_fitness")
        goal_map = {
            "lose_fat": "losing weight and burning fat",
            "build_muscle": "building muscle and strength",
            "general_fitness": "improving overall fitness"
        }
        goal_desc = goal_map.get(goal, "improving overall fitness")
        
        # Build prompt
        prompt = f"""You are a personal fitness trainer providing voice instructions for a workout step.

WORKOUT STEP:
- Title: {step_title}
- Description: {step_description or 'N/A'}
- Instructions: {step_instructions or 'N/A'}
- Duration: {step_duration_sec or 'N/A'} seconds

USER PROFILE:
- Fitness Level: {fitness_level}
- Goal: {goal_desc}

TRAINER PERSONALITY:
- Style: {persona_desc}
- Enthusiasm: {enthusiasm_desc}
- Age Category: {age_cat}/5
- Gender: {gender or 'neutral'}

TASK:
Generate a personalized voice instruction script for this workout step. The script should:
1. Match the {persona_desc} personality style
2. Have {enthusiasm_desc} energy level
3. Be appropriate for a {fitness_level} fitness level
4. Be concise and clear (aim for 10-30 seconds of speech)
5. Include clear instructions for the exercise
6. Be motivating and encouraging
7. Use natural, conversational language suitable for voice delivery

Return ONLY the script text, no explanations or metadata."""

        try:
            response = self.model.generate_content(prompt)
            script = response.text.strip()
            return script
        except Exception as e:
            raise Exception(f"Failed to generate workout script: {str(e)}")

