import os
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import google.generativeai as genai
from openai import OpenAI
from app.types import TimelineItem


class LLMProviderInterface(ABC):
    """Abstract interface for LLM providers"""
    
    @abstractmethod
    def generate_workout_script(
        self,
        timeline_item: TimelineItem,
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate personalized workout script for a step.

        Returns a dict with:
        - intro_text: High-level intro/overview for the step.
        - cue_text: Combined cue sentences that can be spoken at any rep.
        """
        raise NotImplementedError
    
    def _build_prompt(
        self,
        timeline_item: TimelineItem,
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
        number_of_sets = len(timeline_item.get("sets") or []) or 1
        
        # Build prompt
        prompt = f"""You are a personal fitness trainer providing voice instructions for a workout step to a single person.

WORKOUT STEP:
- Title: {timeline_item["title"]}
- Description: {timeline_item.get("description") or 'N/A'}
- Instructions: {timeline_item.get("instructions") or 'N/A'}
- Number of Sets: {number_of_sets}
- Rest Between Sets: {timeline_item.get("rest_between_sets_s") or 0} seconds if sets are used, otherwise single set thus not applicable
- Exercise Type: {timeline_item.get("exercise_type") or 'N/A'}

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

OUTPUT FORMAT:
You must return a valid JSON object with exactly three fields:
- "intro_text": A comprehensive explanation on the workout as a briefing, 
    including how to execute the exercise and what to look out for. About 3 sentences.
- "start_text": Hype the user to start the workout. About 1 sentence.
- "cue_text": A single string with {2 * number_of_sets} cue sentences that can be spoken at any rep. 
The cues are reminders and tips for the user to do the exercise correctly. 
Split the sentences with '<break time="1s" />'.

Return ONLY the JSON object, no explanations or metadata. Example format:
{{"intro_text": "Today we’re dialing in on dumbbell bench presses to build strong, balanced pushing power. Set yourself up with your feet planted, shoulders tucked back, and dumbbells starting at chest level, then press smoothly up and lower with control like you own the weight. Keep things tight and intentional — no rushing, no ego",
  "start_text": "and when you’re ready, let’s get this started.",
  "cue_text": "Before you move, take a moment to lock in your setup and feel your feet pressing into the floor 
  <break time=\"1s\" /> As you lower the weights, stay smooth and controlled, keeping tension through your chest and arms 
  <break time=\"1s\" /> Keep your core lightly braced so your body stays stable and connected on every rep 
  <break time=\"1s\" /> Drive the dumbbells up with steady confidence, not momentum. This is important.
  <break time=\"1s\" /> Keep your shoulders proud and supported by the bench as you press 
  <break time=\"1s\" /> Let your elbows track naturally without flaring too wide 
  <break time=\"1s\" /> You can breathe out as you push through the hardest part of the lift 
  <break time=\"1s\" /> Maintain control from the first rep to the last, even as fatigue builds! 
  <break time=\"1s\" /> Make sure to stay tight from your feet all the way through your hands 
  <break time=\"1s\" /> Own each rep with intention and finish strong!"}}"""

        return prompt
    
    def _parse_json_response(self, response_text: str) -> Dict[str, str]:
        """
        Parse JSON response from LLM, handling potential markdown code blocks or extra text.
        
        Args:
            response_text: Raw text response from LLM
            
        Returns:
            Dict with 'intro_text', 'start_text' and 'cue_text' keys
            
        Raises:
            Exception: If JSON parsing fails
        """
        # Clean the response - remove markdown code blocks if present
        cleaned = response_text.strip()
        
        # Try to extract JSON from markdown code blocks
        if "```json" in cleaned:
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        # Try to find JSON object in the text
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            cleaned = cleaned[start_idx:end_idx + 1]
        
        try:
            result = json.loads(cleaned)
            # Validate required fields
            if "intro_text" not in result or "start_text" not in result or "cue_text" not in result:
                raise ValueError("Missing required fields: intro_text, start_text or cue_text")
            return {"intro_text": str(result["intro_text"]), "start_text": str(result["start_text"]), "cue_text": str(result["cue_text"])}
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON response: {str(e)}. Response was: {cleaned[:200]}")
        except ValueError as e:
            raise Exception(f"Invalid response format: {str(e)}. Response was: {cleaned[:200]}")


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
    ) -> Dict[str, str]:
        """Generate personalized workout script using Gemini."""
        prompt = self._build_prompt(
            step_title, step_description, step_instructions,
            step_duration_sec, user_profile, trainer_config
        )

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
        except Exception as e:
            raise Exception(f"Failed to generate workout script with Gemini: {str(e)}")

        # Parse JSON response
        return self._parse_json_response(response_text)


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
        timeline_item: TimelineItem,
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate personalized workout script using OpenAI."""
        prompt = self._build_prompt(
            timeline_item, user_profile, trainer_config
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional fitness trainer creating voice instructions for workouts. Always respond with valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            response_text = response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Failed to generate workout script with OpenAI: {str(e)}")

        # Parse JSON response
        return self._parse_json_response(response_text)
