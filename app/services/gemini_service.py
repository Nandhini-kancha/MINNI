import logging
import re
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.system_prompts import MINNI_SYSTEM_PROMPT

logger = logging.getLogger("minni.gemini_service")


class GeminiService:
    """Service to communicate with Google Gemini API for natural-language & audio generation."""

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
        """Generates response using Gemini API with automatic model fallback for missing key, quota limits, or API errors."""
        audience_instruction = self._get_audience_instruction(audience)
        
        telugu_instruction = (
            "\nLANGUAGE REQUIREMENT: The user may ask questions in Telugu script or Romanized Telugu (Teluglish). "
            "If the question is in Telugu or Teluglish, you MUST respond in friendly, clear, warm Telugu so they understand easily!"
        )

        full_system_instruction = f"{MINNI_SYSTEM_PROMPT}\n{audience_instruction}\n{telugu_instruction}\nIntent category: {intent}"

        # If Gemini API Key is configured, attempt real Gemini API call
        if settings.is_gemini_configured():
            candidate_models = [self.model_name, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]
            candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

            for model_id in candidate_models:
                try:
                    from google import genai
                    from google.genai import types

                    client = genai.Client(api_key=settings.GEMINI_API_KEY)
                    
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
                        model=model_id,
                        contents=contents,
                        config=config,
                    )

                    if response and response.text:
                        return response.text.strip()

                except Exception as e:
                    logger.warning(f"Gemini API model {model_id} notice: {e}")

        # Fallback generator if API key is unconfigured or rate limited
        return self._generate_fallback_response(message, intent, audience)

    def generate_response_from_audio(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/wav",
        session_history: Optional[List[Dict[str, str]]] = None,
        audience: str = "general"
    ) -> str:
        """Processes raw audio file bytes directly using Gemini's native multimodal audio API."""
        audience_instruction = self._get_audience_instruction(audience)
        full_system_instruction = (
            f"{MINNI_SYSTEM_PROMPT}\n{audience_instruction}\n"
            "TASK: Listen to the audio input carefully. Understand the user's spoken question about body safety, boundaries, "
            "strangers, or bullying (in English, Telugu, or Teluglish) and provide a warm, protective, age-appropriate response."
        )

        if settings.is_gemini_configured():
            candidate_models = [self.model_name, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash-latest"]
            candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

            for model_id in candidate_models:
                try:
                    from google import genai
                    from google.genai import types

                    client = genai.Client(api_key=settings.GEMINI_API_KEY)

                    contents = [
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                                types.Part.from_text(text="Please answer this spoken voice recording about safety.")
                            ]
                        )
                    ]

                    config = types.GenerateContentConfig(
                        system_instruction=full_system_instruction,
                        temperature=0.7,
                        max_output_tokens=1000,
                    )

                    response = client.models.generate_content(
                        model=model_id,
                        contents=contents,
                        config=config,
                    )

                    if response and response.text:
                        return response.text.strip()

                except Exception as e:
                    logger.warning(f"Audio Gemini model {model_id} notice: {e}")

        # Fallback audio response
        return self._generate_fallback_response("Voice message received", "body_safety", audience)

    def _generate_fallback_response(self, message: str, intent: str, audience: str) -> str:
        """Rule-based fallback generator for Minni supporting English and Telugu."""
        msg_lower = message.lower().strip()
        is_telugu = bool(re.search(r"[\u0C00-\u0C7F]", message)) or any(w in msg_lower for w in ["naku", "taakidi", "chedu", "manchi", "nannu", "edipistunnaru", "teliyani", "bhayanga", "gurinchi", "chey", "cheppandi"])

        if is_telugu:
            if intent in ["body_safety", "general_education", "unsafe_situation"] or any(w in msg_lower for w in ["good", "bad", "touch", "rules", "safety"]):
                return (
                    "నమస్కారం! మీ రక్షణ గురించి మిన్నీ వివరంగా చెప్తోంది. గుర్తుంచుకోండి, మీ శరీరం మీ స్వంతం.\n\n"
                    "**1. మంచి తాకిడి (Good Touch)**: మీకు సంతోషం, భద్రత మరియు ప్రేమపూర్వక భావన కలిగిస్తుంది (ఉదాహరణకు అమ్మ లేదా నాన్న ఇచ్చే ముద్దు లేదా హగ్).\n\n"
                    "**2. చెడు తాకిడి (Bad Touch)**: మీ ప్రైవేట్ భాగాలను ఎవరైనా తాకినా లేదా మీకు భయం, అసౌకర్యం కలిగించినా అది చెడు తాకిడి.\n\n"
                    "**మిన్నీ 3 ముఖ్యమైన రక్షణ నియమాలు (3 Safety Rules)**:\n"
                    "1. **వద్దు! (SAY NO!)**: గట్టిగా వద్దని చెప్పండి.\n"
                    "2. **పరిగెత్తండి (RUN AWAY)**: సురక్షిత ప్రాంతానికి వెళ్ళండి.\n"
                    "3. **పెద్దలకు చెప్పండి (TELL A TRUSTED ADULT)**: మీ తల్లిదండ్రులు లేదా ఉపాధ్యాయులకు వెంటనే చెప్పండి. ఇది మీ తప్పు కాదు!"
                )
            elif intent == "stranger_safety":
                return (
                    "అపరిచితుల భద్రత చాలా ముఖ్యం!\n\n"
                    "1. తెలియని వ్యక్తులతో ఎక్కడికీ వెళ్ళకూడదు.\n"
                    "2. అపరిచితులు ఇచ్చే చాక్లెట్లు లేదా బహుమతులు తీసుకోకూడదు.\n"
                    "3. ఎవ‌రైనా మిమ్మల్ని భయపెడితే వెంటనే మీ తల్లిదండ్రులకు లేదా ఉపాధ్యాయులకు చెప్పండి!"
                )
            else:
                return (
                    "నమస్కారం! నేను మిన్నీ (Minni). మీ రక్షణ మరియు భద్రత నా బాధ్యత.\n\n"
                    "మీకు ఎలాంటి భయం లేదా అసౌకర్యం అనిపించినా వెంటనే మీ నమ్మకమైన పెద్దలకు చెప్పండి లేదా హెల్ప్‌లైన్ **1098 / 112** కి కాల్ చేయండి!"
                )

        if intent == "greeting" or re.search(r"\b(hi|hello|hey|who are you)\b", msg_lower):
            return (
                "Hello there! I am **Minni**, your friendly AI safety companion. 😊\n\n"
                "I am here to help you learn about **body safety**, **good touch & bad touch**, "
                "**stranger safety**, **bullying**, and **staying safe online**.\n\n"
                "You can ask me any question in English or Telugu!"
            )
        elif intent == "body_safety":
            return (
                "Hi there! Remember, your body belongs to YOU and you have the right to feel safe all the time.\n\n"
                "A **good touch** makes you feel happy, safe, and cared for (like a high-five or a hug from mom or dad). "
                "An **uncomfortable or bad touch** makes you feel confused, scared, sad, or uncomfortable.\n\n"
                "If anyone ever tries to touch your private parts or asks you to touch theirs:\n"
                "1. **Say NO!** clearly and firmly.\n"
                "2. **GO AWAY / RUN** to a safe place.\n"
                "3. **TELL** a trusted adult (like a parent, teacher, or guardian) right away. You will NEVER be in trouble for telling!"
            )
        elif intent == "stranger_safety":
            return (
                "Stranger safety is super important!\n\n"
                "A stranger is simply anyone you and your family don't know well. Most strangers are nice, but we must follow safety rules:\n"
                "1. **Never go anywhere with a stranger** or get into their car.\n"
                "2. **Never accept gifts, candy, or secrets** from strangers.\n"
                "3. If a stranger approaches you or makes you feel unsafe, step back, say NO, run to a safe adult (like a store manager or police officer), and tell your trusted adult."
            )
        elif intent == "bullying_harassment":
            return (
                "I am so sorry you are dealing with this. Please know that bullying or harassment is NEVER your fault.\n\n"
                "Here is what you can do:\n"
                "1. **Stay calm and walk away** from bullies to a safe area with other people.\n"
                "2. **Tell a trusted adult** (a parent, teacher, school counselor, or principal) who can help stop the behavior.\n"
                "3. You deserve to be treated with respect, kindness, and dignity!"
            )
        elif intent == "online_safety":
            return (
                "Staying safe online is just as important as staying safe in person!\n\n"
                "Key Rules for Online Safety:\n"
                "1. **Keep Private Info Private**: Never share your full name, address, school, phone number, or passwords online.\n"
                "2. **Online Friends are Strangers**: Never agree to meet someone in person that you only met online.\n"
                "3. **Tell a Trusted Adult**: If anything online makes you feel sad, scared, or uncomfortable, tell an adult right away."
            )
        elif intent == "unsafe_situation":
            return (
                "If you ever feel unsafe or lost, stay calm. Here is what to do:\n\n"
                "1. Look for a person in uniform (police officer, store staff, security guard) or a parent with children.\n"
                "2. Stay in a bright, open place where there are other people.\n"
                "3. Tell a trusted adult or call emergency helplines (**112 / 1098**) right away. Your safety comes first!"
            )
        else:
            return (
                f"Hello! Minni is here to support you. You asked: '{message}'.\n\n"
                "Always remember to stay curious, treat yourself and others with kindness, "
                "and reach out to a trusted adult whenever you feel unsure or need support! 💖"
            )


# Global instance
gemini_service = GeminiService()
