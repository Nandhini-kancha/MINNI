import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.system_prompts import MINNI_SYSTEM_PROMPT

logger = logging.getLogger("minni.gemini_service")


class GeminiService:
    """Service to communicate with Google Gemini API for natural-language generation."""

    def __init__(self):
        self.model_name = settings.GEMINI_MODEL

    def _get_audience_instruction(self, audience: str = "general") -> str:
        """Return additional audience context based on user profile."""
        if audience == "child":
            return (
                "\nAUDIENCE: You are speaking to a CHILD. Use simple, warm, gentle language. "
                "Keep sentences short and easy to understand. Emphasize talking to a trusted adult."
            )
        elif audience == "woman":
            return (
                "\nAUDIENCE: You are speaking to a WOMAN. Provide supportive, empathetic, "
                "empowering, and clear practical advice on safety, boundaries, and support resources."
            )
        return "\nAUDIENCE: General safety inquiry. Keep tone friendly, supportive, clear, and age-appropriate."

    def generate_response(
        self,
        message: str,
        intent: str,
        session_history: Optional[List[Dict[str, str]]] = None,
        audience: str = "general"
    ) -> str:
        """Generates response using Gemini API with fallback for missing key or API errors."""
        audience_instruction = self._get_audience_instruction(audience)
        full_system_instruction = f"{MINNI_SYSTEM_PROMPT}\n{audience_instruction}\nIntent category: {intent}"

        # If Gemini API Key is configured, attempt real Gemini API call
        if settings.is_gemini_configured():
            # Try new google-genai SDK first
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                
                # Build contents array from session history
                contents = []
                if session_history:
                    for turn in session_history:
                        role = "user" if turn["role"] == "user" else "model"
                        contents.append(types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=turn["content"])]
                        ))
                
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=message)]
                ))

                config = types.GenerateContentConfig(
                    system_instruction=full_system_instruction,
                    temperature=0.7,
                    max_output_tokens=1000,
                )

                response = client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )

                if response and response.text:
                    return response.text.strip()

            except Exception as e:
                logger.warning(f"google-genai SDK call failed, trying google-generativeai: {e}")
                try:
                    import google.generativeai as genai_legacy
                    genai_legacy.configure(api_key=settings.GEMINI_API_KEY)
                    
                    model = genai_legacy.GenerativeModel(
                        model_name=self.model_name if "gemini" in self.model_name else "gemini-1.5-flash",
                        system_instruction=full_system_instruction
                    )
                    
                    # Convert history format for legacy sdk
                    history_formatted = []
                    if session_history:
                        for turn in session_history:
                            role = "user" if turn["role"] == "user" else "model"
                            history_formatted.append({"role": role, "parts": [turn["content"]]})

                    chat = model.start_chat(history=history_formatted)
                    res = chat.send_message(message)
                    if res and res.text:
                        return res.text.strip()
                except Exception as ex:
                    logger.error(f"Gemini API generation error: {ex}")

        # Fallback generator if API key is not configured or network call failed
        return self._generate_fallback_response(message, intent, audience)

    def _generate_fallback_response(self, message: str, intent: str, audience: str) -> str:
        """Rule-based fallback generator for Minni when Gemini API key is unconfigured or offline."""
        if intent == "body_safety":
            return (
                "Hi there! Remember, your body belongs to YOU and you have the right to feel safe all the time.\n\n"
                "A **good touch** makes you feel happy, safe, and cared for (like a high-five or a hug from mom or dad). "
                "An **uncomfortable or bad touch** makes you feel confused, scared, sad, or uncomfortable.\n\n"
                "If anyone ever tries to touch your private parts (the parts covered by a swimsuit) or asks you to touch theirs:\n"
                "1. **Say NO!** clearly and firmly.\n"
                "2. **GO AWAY** to a safe place.\n"
                "3. **TELL** a trusted adult (like a parent or teacher) immediately. You will never be in trouble for telling!"
            )
        elif intent == "stranger_safety":
            return (
                "Stranger safety is super important!\n\n"
                "A stranger is simply anyone you and your family don't know well. Most strangers are nice, but we must always follow safety rules:\n"
                "1. Never go anywhere with a stranger or get into their car.\n"
                "2. Never accept gifts, candy, or secrets from strangers.\n"
                "3. If a stranger approaches you or makes you feel unsafe, step back, say NO, run to a safe adult (like a shop manager or police officer), and tell your trusted adult."
            )
        elif intent == "bullying_harassment":
            return (
                "I am so sorry you are dealing with this. Please know that bullying or harassment is NEVER your fault.\n\n"
                "Here is what you can do:\n"
                "1. Stay calm and walk away from bullies to a safe area.\n"
                "2. Do not keep it inside. Talk to a trusted adult, teacher, or counselor who can help stop the behavior.\n"
                "3. You deserve to be treated with respect, kindness, and dignity."
            )
        elif intent == "online_safety":
            return (
                "Staying safe online is just as important as staying safe in person!\n\n"
                "Key Rules for Online Safety:\n"
                "1. **Keep Private Info Private**: Never share your full name, address, school, phone number, or passwords online.\n"
                "2. **Don't talk to strangers**: Online friends are still strangers if you haven't met them in real life.\n"
                "3. **Tell a Trusted Adult**: If anything online makes you feel sad, scared, or uncomfortable, tell an adult right away."
            )
        elif intent == "unsafe_situation":
            return (
                "If you ever feel unsafe or lost, stay calm. Here is what to do:\n\n"
                "1. Look for a person in uniform (police officer, store staff, security guard) or a mom with children.\n"
                "2. Stay in a bright, open place where there are other people.\n"
                "3. Contact or tell a trusted adult immediately. Your safety comes first!"
            )
        else:
            return (
                f"Hello! Minni is here to help and keep you safe. You asked about: '{message}'.\n\n"
                "Always remember to stay curious, treat yourself and others with kindness, "
                "and reach out to trusted adults whenever you feel unsure or need support!"
            )


# Global instance
gemini_service = GeminiService()
