import re
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
        """Generates response using Gemini API with automatic model fallback for missing key, quota limits, or API errors."""
        audience_instruction = self._get_audience_instruction(audience)
        full_system_instruction = f"{MINNI_SYSTEM_PROMPT}\n{audience_instruction}\nIntent category: {intent}"

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

    def _generate_fallback_response(self, message: str, intent: str, audience: str) -> str:
        """Rule-based fallback generator for Minni providing bilingual Telugu and English safety responses."""
        msg_lower = message.lower().strip()
        is_telugu = bool(re.search(r"[\u0c00-\u0c7f]", message)) or any(w in msg_lower for w in ["sparsha", "namaskaram", "sahayam", "chedu"])

        if is_telugu:
            if intent == "body_safety":
                return (
                    "నమస్కారం! గుర్తుంచుకోండి, మీ శరీరం మీ స్వంతం. ఎల్లప్పుడూ సురక్షితంగా ఉండే హక్కు మీకు ఉంది. 😊\n\n"
                    "• **మంచి స్పర్శ (Good Touch)**: మిమ్మల్ని సంతోషంగా, సురక్షితంగా ఉంచుతుంది (ఉదాహరణకు అమ్మ లేదా నాన్న ఇచ్చే కౌగిలింత).\n"
                    "• **చెడు స్పర్శ (Bad Touch)**: మిమ్మల్ని గందరగోళానికి, భయానికి లేదా అసౌకర్యానికి గురిచేస్తుంది.\n\n"
                    "ఎవరైనా మీ ప్రైవేట్ భాగాలను తాకడానికి ప్రయత్నిస్తే లేదా మిమ్మల్ని తాకమని అడిగితే:\n"
                    "1. **వద్దు! (SAY NO!)** అని గట్టిగా చెప్పండి.\n"
                    "2. **పరుగెత్తండి (RUN AWAY)** - సురక్షిత ప్రాంతానికి వెళ్ళండి.\n"
                    "3. **చెప్పండి (TELL)** - మీరు నమ్మే పెద్దలకు (తల్లిదండ్రులు, ఉపాధ్యాయులు) వెంటనే చెప్పండి. మీరు చెప్పినందుకు మీపై ఎవరూ కోప్పడరు!"
                )
            elif intent == "stranger_safety":
                return (
                    "అపరిచితుల నుండి భద్రత చాలా ముఖ్యం!\n\n"
                    "మీ కుటుంబానికి తెలియని వ్యక్తి అపరిచితుడు. అత్యవసర భద్రతా నియమాలు పాటించండి:\n"
                    "1. **అపరిచితులతో ఎక్కడికీ వెళ్లవద్దు** లేదా వారి కార్లలో ఎక్కవద్దు.\n"
                    "2. **బహుమతులు లేదా మిఠాయిలు తీసుకోవద్దు**.\n"
                    "3. ఎవరైనా మిమ్మల్ని భయపెడితే, వద్దు అని చెప్పి వెంటనే పోలీసులకు లేదా ఉపాధ్యాయులకు చెప్పండి."
                )
            else:
                return (
                    f"నమస్కారం! నేను **మిన్ని (Minni)**. మీ ప్రశ్న: '{message}'.\n\n"
                    "మీరు ఎల్లప్పుడూ సురక్షితంగా ఉండాలి. శరీరం మరియు ఆన్‌లైన్ భద్రత గురించి ఏవైనా అనుమానాలు ఉంటే మీరు నమ్మే పెద్దలకు లేదా చైల్డ్ హెల్ప్‌లైన్ **1098** కి వెంటనే చెప్పండి! 💖"
                )

        if intent == "greeting" or any(w in msg_lower for w in ["hi", "hello", "hey", "who are you"]):
            return (
                "Hello there! I am **Minni**, your friendly AI safety companion. 😊\n\n"
                "I understand **Telugu (తెలుగు)** and **English**! I am here to help you learn about **body safety**, **good touch & bad touch**, "
                "**stranger safety**, **bullying**, and **staying safe online**.\n\n"
                "You can ask me any question in Telugu or English!"
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
