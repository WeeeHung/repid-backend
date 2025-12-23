import os
import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
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
    
    @abstractmethod
    def generate_brief_script(
        self,
        workout_title: str,
        workout_description: Optional[str],
        estimated_duration_sec: Optional[int],
        timeline_items: List[TimelineItem],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """
        Generate start brief script to mentally prepare the user for the workout session.
        
        Returns:
            Brief text that explains what will happen in today's session and prepares the user mentally.
        """
        raise NotImplementedError
    
    @abstractmethod
    def generate_debrief_script(
        self,
        workout_title: str,
        timeline_items: List[TimelineItem],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """
        Generate end debrief script to summarize achievements and provide post-workout guidance.
        
        Returns:
            Debrief text that summarizes what was accomplished, praises the user, and provides next steps (nutrition, rest, etc.).
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
    
    def _build_brief_prompt(
        self,
        workout_title: str,
        workout_description: Optional[str],
        estimated_duration_sec: Optional[int],
        timeline_items: List[TimelineItem],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Build the prompt for brief script generation"""
        fitness_level = user_profile.get("fitness_level", "intermediate")
        goal = user_profile.get("goal", "general_fitness")
        goal_map = {
            "lose_fat": "fat loss and conditioning",
            "build_muscle": "strength and muscle development",
            "general_fitness": "overall fitness and wellness"
        }
        goal_desc = goal_map.get(goal, "overall fitness and wellness")
        
        # Build exercise list
        exercise_list = "\n".join([f"- {item.get('title', 'N/A')}" for item in timeline_items])
        duration_min = (estimated_duration_sec // 60) if estimated_duration_sec else None
        duration_text = f"{duration_min} minutes" if duration_min else "this session"
        
        prompt = f"""You are a premium personal fitness coach preparing a user for their workout session. Your tone is confident, warm, and motivating. You speak with steady energy — engaged but not overhyped. Authority comes from clarity and certainty, not volume or exaggeration.

GUIDELINES:
- Use short, purposeful sentences with natural warmth
- Avoid filler, jokes, emojis, slang, or excessive exclamation marks
- No motivational clichés or generic hype phrases
- Be grounded but not flat — maintain steady engagement
- Assume the user is disciplined and capable
- Focus on mental preparation and setting clear expectations
- Encourage focus, intention, and presence
- Speak like a trusted coach who believes in the user

WORKOUT SESSION:
- Title: {workout_title}
- Description: {workout_description or 'N/A'}
- Estimated Duration: {duration_text}
- Exercises: {len(timeline_items)} exercises
{exercise_list}

USER PROFILE:
- Fitness Level: {fitness_level}
- Goal: {goal_desc}

TASK:
Generate a start brief that:
1. Welcomes the user and explains what will happen in today's session
2. Mentally prepares them for the workout ahead
3. Motivates them if necessary (but keep it grounded, not hype)
4. Sets clear expectations about the session
5. Prepares them to begin with the warm-up right after this brief
6. Uses natural, conversational language suitable for voice delivery
7. Does not use any markdown formatting, emojis, or excessive punctuation

The brief should be 6-10 sentences. It should feel like a coach speaking directly to the user, preparing them mentally and physically for the work ahead. After this brief, the warm-up will start immediately.

Return ONLY the brief text, no JSON, no explanations, no metadata."""
        
        return prompt
    
    def _build_debrief_prompt(
        self,
        workout_title: str,
        timeline_items: List[TimelineItem],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Build the prompt for debrief script generation"""
        fitness_level = user_profile.get("fitness_level", "intermediate")
        goal = user_profile.get("goal", "general_fitness")
        goal_map = {
            "lose_fat": "fat loss and conditioning",
            "build_muscle": "strength and muscle development",
            "general_fitness": "overall fitness and wellness"
        }
        goal_desc = goal_map.get(goal, "overall fitness and wellness")
        
        # Build exercise list
        exercise_list = "\n".join([f"- {item.get('title', 'N/A')}" for item in timeline_items])
        
        prompt = f"""You are a premium personal fitness coach congratulating a user after completing their workout session. Your tone is warm, proud, and supportive. You speak with genuine appreciation for their effort.

GUIDELINES:
- Use short, purposeful sentences with natural warmth
- Avoid filler, jokes, emojis, slang, or excessive exclamation marks
- No motivational clichés or generic hype phrases
- Be genuine and specific in your praise
- Acknowledge their effort and completion
- Provide practical post-workout guidance
- Speak like a trusted coach who cares about their recovery and progress

WORKOUT SESSION COMPLETED:
- Title: {workout_title}
- Exercises Completed: {len(timeline_items)} exercises
{exercise_list}

USER PROFILE:
- Fitness Level: {fitness_level}
- Goal: {goal_desc}

TASK:
Generate an end debrief that:
1. Summarizes what they accomplished today (briefly mention key exercises)
2. Praises them genuinely for completing the session
3. Provides practical post-workout guidance:
   - Nutrition/hydration reminders
   - Rest and recovery advice
   - What to do next
4. Ends with a warm goodbye message (e.g., "See you for the next workout and rest well!")
5. Uses natural, conversational language suitable for voice delivery
6. Does not use any markdown formatting, emojis, or excessive punctuation

The debrief should be 8-12 sentences. It should feel like a coach acknowledging their hard work and caring about their recovery. End with a warm farewell.

Return ONLY the debrief text, no JSON, no explanations, no metadata."""
        
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
    
    def generate_brief_script(
        self,
        workout_title: str,
        workout_description: Optional[str],
        estimated_duration_sec: Optional[int],
        timeline_items: List[TimelineItem],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Generate start brief script using Gemini."""
        prompt = self._build_brief_prompt(
            workout_title, workout_description, estimated_duration_sec,
            timeline_items, user_profile, trainer_config
        )
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Failed to generate brief script with Gemini: {str(e)}")
    
    def generate_debrief_script(
        self,
        workout_title: str,
        timeline_items: List[TimelineItem],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Generate end debrief script using Gemini."""
        prompt = self._build_debrief_prompt(
            workout_title, timeline_items, user_profile, trainer_config
        )
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Failed to generate debrief script with Gemini: {str(e)}")


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
    
    def generate_brief_script(
        self,
        workout_title: str,
        workout_description: Optional[str],
        estimated_duration_sec: Optional[int],
        timeline_items: List[TimelineItem],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Generate start brief script using OpenAI."""
        prompt = self._build_brief_prompt(
            workout_title, workout_description, estimated_duration_sec,
            timeline_items, user_profile, trainer_config
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional fitness trainer creating voice instructions for workouts. Always respond with plain text only, no JSON, no markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Failed to generate brief script with OpenAI: {str(e)}")
    
    def generate_debrief_script(
        self,
        workout_title: str,
        timeline_items: List[TimelineItem],
        user_profile: Dict[str, Any],
        trainer_config: Dict[str, Any]
    ) -> str:
        """Generate end debrief script using OpenAI."""
        prompt = self._build_debrief_prompt(
            workout_title, timeline_items, user_profile, trainer_config
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional fitness trainer creating voice instructions for workouts. Always respond with plain text only, no JSON, no markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=400,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Failed to generate debrief script with OpenAI: {str(e)}")
