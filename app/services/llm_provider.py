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
        # Build user context
        fitness_level = user_profile.get("fitness_level", "intermediate")
        goal = user_profile.get("goal", "general_fitness")
        goal_map = {
            "lose_fat": "fat loss and conditioning",
            "build_muscle": "strength and muscle development",
            "general_fitness": "overall fitness and wellness"
        }
        goal_desc = goal_map.get(goal, "overall fitness and wellness")
        number_of_sets = len(timeline_item.get("sets") or []) or 1
        
        # Build prompt
        prompt = f"""You are a premium personal fitness coach guiding a user through a physical wellness session. Your tone is confident, warm, and present. You speak with steady energy — engaged but not overhyped. Authority comes from clarity and certainty, not volume or exaggeration.

GUIDELINES:
- Use short, purposeful sentences with natural warmth
- Avoid filler, jokes, emojis, slang, or excessive exclamation marks
- No motivational clichés or generic hype phrases
- Be grounded but not flat — maintain steady engagement
- Assume the user is disciplined and capable
- Focus on form, breath, rhythm, and awareness
- Encourage control and intention over aggression
- Speak like a trusted coach who believes in the user

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

TASK:
Generate a voice instruction script for this workout step. The script should:
1. Be confident, clear, and warmly engaged — not flat or detached
2. Be appropriate for a {fitness_level} fitness level
3. Focus on proper form, breathing, and body awareness
4. Use natural, conversational language suitable for voice delivery
5. Do not use any markdown formatting, emojis, or excessive punctuation

OUTPUT FORMAT:
You must return a valid JSON object with exactly three fields:
- "intro_text": A thorough pep talk into starting this exercise. Ensure the user is clear on the exercise, covering form, breathing, muscle engagement, and key points to focus on. Be detailed and instructive. 5-8 sentences.
- "start_text": A calm, composed cue to begin. One short sentence, no hype.
- "cue_text": IF Exercise type is "durations", provide {2 * number_of_sets} cue sentences focused on form, breath, and rhythm. Split with '<break time="1s" />'. Otherwise return an empty string.

Return ONLY the JSON object, no explanations or metadata. Example format:
{{"intro_text": "This is the dumbbell bench press. You will build balanced pushing strength through controlled movement. Set your feet flat, draw your shoulders back into the bench, and hold the dumbbells at chest level. Press upward with intention, then lower slowly. Focus on stability and breath throughout.",
  "start_text": "Begin when you are ready.",
  "cue_text": "Ground your feet and feel the bench supporting your back <break time=\"1s\" /> Lower the weights with control, keeping tension through your chest <break time=\"1s\" /> Breathe out as you press upward <break time=\"1s\" /> Keep your core engaged and your body stable <break time=\"1s\" /> Let your elbows track naturally, not too wide <break time=\"1s\" /> Maintain steady rhythm from start to finish"}}
  OR
  {{"intro_text": "This is the dumbbell bench press. You will build balanced pushing strength through controlled movement. Set your feet flat, draw your shoulders back into the bench, and hold the dumbbells at chest level. Press upward with intention, then lower slowly. Focus on stability and breath throughout.",
  "start_text": "Begin when you are ready.",
  "cue_text": ""}}"""

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
