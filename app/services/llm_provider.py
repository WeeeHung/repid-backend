import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import google.generativeai as genai
from openai import OpenAI


class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers"""
    
    @abstractmethod
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
        raise NotImplementedError


class GeminiProvider(LLMProviderInterface):
    """Google Gemini LLM provider implementation"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini provider
        
        Args:
            api_key: Google Gemini API key
            model_name: Model to use (default: gemini-2.0-flash-exp)
        """
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    def generate_workout_script(
        self,
        step_title: str,
        step_description: Optional[str],
        step_instructions: Optional[str],
        step_duration_sec: Optional[int],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Generate personalized workout script using Gemini"""
        prompt = self._build_prompt(
            step_title, step_description, step_instructions, 
            step_duration_sec, user_profile, trainer_config
        )
        
        try:
            response = self.model.generate_content(prompt)
            script = response.text.strip().replace("*", "")
            return script
        except Exception as e:
            raise Exception(f"Failed to generate workout script with Gemini: {str(e)}")
    
    def _build_prompt(
        self,
        step_title: str,
        step_description: Optional[str],
        step_instructions: Optional[str],
        step_duration_sec: Optional[int],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Build the prompt for workout script generation"""
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
        prompt = f"""You are a personal fitness trainer providing voice instructions for a workout step to a single person.

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
8. Do not use any markdown formatting (e.g., **bold**), just plain text.

Return ONLY the script text, no explanations or metadata."""

        return prompt


class OpenAIProvider(LLMProviderInterface):
    """OpenAI LLM provider implementation"""
    
    def __init__(self, api_key: str, model_name: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key
            model_name: Model to use (default: gpt-4o-mini)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key)
    
    def generate_workout_script(
        self,
        step_title: str,
        step_description: Optional[str],
        step_instructions: Optional[str],
        step_duration_sec: Optional[int],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Generate personalized workout script using OpenAI"""
        prompt = self._build_prompt(
            step_title, step_description, step_instructions, 
            step_duration_sec, user_profile, trainer_config
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a professional fitness trainer creating voice instructions for workouts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            script = response.choices[0].message.content.strip().replace("*", "")
            return script
        except Exception as e:
            raise Exception(f"Failed to generate workout script with OpenAI: {str(e)}")
    
    def _build_prompt(
        self,
        step_title: str,
        step_description: Optional[str],
        step_instructions: Optional[str],
        step_duration_sec: Optional[int],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Build the prompt for workout script generation"""
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
        prompt = f"""You are a personal fitness trainer providing voice instructions for a workout step to a single person.

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
8. Do not use any markdown formatting (e.g., **bold**), just plain text.
9. Make it fun and engaging with some light-hearted jokes.

Return ONLY the script text, no explanations or metadata."""

        return prompt
