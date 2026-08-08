import re
from typing import Dict, Tuple, Optional


class SafetyService:
    """Safety and Intent Classification Layer for Minni.
    
    Supports English, Telugu script, and Romanized Teluglish inputs.
    Categorizes incoming user messages, evaluates risk levels, and provides
    pre-defined safe emergency responses for high-risk situations before invoking LLMs.
    """

    # High Risk Emergency Patterns (English + Telugu Script + Teluglish)
    HIGH_RISK_PATTERNS = [
        r"\b(suicide|kill my\s*self|end my life|want to die|cutting my\s*self)\b",
        r"\b(someone is (hitting|beating|touching|following|chasing|abusing).*?(me|us))\b",
        r"\b(touching me|touches me|touched me).*?(inappropriately|private|secret|wrong)\b",
        r"\b(being abused|physical abuse|sexual abuse|raped|assaulted|molested)\b",
        r"\b(locked in|trapped in|kidnapped|held against my will)\b",
        r"\b(in danger|help me please|he has a weapon|gun|knife|scared right now)\b",
        r"\b(forced to touch|touching my private|uncomfortable touch right now)\b",
        # Telugu Script & Teluglish High Risk Keywords
        r"(నన్ను కొడుతున్నారు|నన్ను హింసిస్తున్నారు|చంపేస్తా|నన్ను పట్టుకున్నారు|భయంగా ఉంది|రక్షించండి|నన్ను తాకుతున్నారు|హింస)",
        r"\b(nannu kottutunnaru|nannu bhayapedutunnaru|nannu taakutunnaru|nannu himsistunnaru|champestanu|sahayam kavali|nannu taakithe)\b",
    ]

    BODY_SAFETY_PATTERNS = [
        r"\b(good touch|bad touch|uncomfortable touch|private parts|swimsuit rule)\b",
        r"\b(body boundaries|my body|touch me|inappropriate touch|personal space)\b",
        r"\b(can someone touch|is it ok if someone touches|touching)\b",
        # Telugu Body Safety Keywords
        r"(చెడు తాకిడి|మంచి తాకిడి|రహస్య తాకిడి|శరీర భాగాలు|తాకడం|తాకిడి|నా శరీరం)",
        r"\b(chedu taakidi|manchi taakidi|bad touch|good touch|rahasya taakidi|naa sareeram|taakidi)\b",
    ]

    STRANGER_SAFETY_PATTERNS = [
        r"\b(stranger|unknown person|someone I don't know|stranger danger)\b",
        r"\b(car ride|offered candy|follow a stranger|lost in store|lost in public)\b",
        # Telugu Stranger Safety Keywords
        r"(తెలియని వ్యక్తులు|అపరిచితులు|కారులో రమ్మన్నారు|చాక్లెట్ ఇచ్చారు)",
        r"\b(aparichithulu|teliyani vallu|car lo rammannaru|stranger)\b",
    ]

    BULLYING_PATTERNS = [
        r"\b(bully|bullying|teasing|cyberbullying|mean kids|harass|harassment)\b",
        r"\b(calling me names|threatened me at school|making fun of me|mean to me)\b",
        # Telugu Bullying Keywords
        r"(నన్ను ఏడిపిస్తున్నారు|స్కూల్లో ఏడిపిస్తున్నారు|అవమానిస్తున్నారు|ఏడిపించడం)",
        r"\b(nannu edipistunnaru|school lo edipistunnaru|bullying)\b",
    ]

    ONLINE_SAFETY_PATTERNS = [
        r"\b(online|internet|social media|password|sharing photos|online friend)\b",
        r"\b(cyber|stranger online|chat room|game chat|private info online)\b",
        # Telugu Online Safety Keywords
        r"(ఆన్‌లైన్|ఇంటర్నెట్|పాస్‌వర్డ్|ఫోటోలు పంపడం)",
        r"\b(online safety|internet safety|password share)\b",
    ]

    UNSAFE_SITUATION_PATTERNS = [
        r"\b(unsafe|scared|feeling uncomfortable|dark street|home alone)\b",
        r"\b(emergency|what to do if|lost|separated from mom|danger)\b",
        # Telugu Unsafe Situation Keywords
        r"(అభద్రత|భయం|రక్షణ|ప్రమాదం)",
        r"\b(bhayanga undi|pramadam|rakshana)\b",
    ]

    GREETING_PATTERNS = [
        r"^(hi|hello|hey|hey minni|good morning|good afternoon|good evening|who are you|what can you do|నమస్కారం|హలో|హాయ్)$"
    ]

    # High Risk Predefined Emergency Responses (Bilingual: English + Telugu)
    EMERGENCY_RESPONSES = {
        "child": (
            "I hear you, and I want you to know that you are brave for speaking up. "
            "Your safety is the most important thing right now.\n\n"
            "మీరు ధైర్యంగా ఉన్నందుకు అభినందనలు. మీ రక్షణే మాకు అత్యంత ముఖ్యం.\n\n"
            "Here is what you should do right now / వెంటనే చేయవలసిన పనులు:\n"
            "1. **Say NO / వద్దు అని చెప్పండి**: Get to a safe place immediately.\n"
            "2. **Tell a Trusted Adult / నమ్మకమైన పెద్దలకు చెప్పండి**: Tell a parent, teacher, or police officer right now.\n"
            "3. **Call Helpline / హెల్ప్‌లైన్‌కి కాల్ చేయండి**: Call Childline at **1098** or Emergency Services at **112 / 911**.\n\n"
            "You are not alone, and it is NOT your fault! మీరు ఒంటరిగా లేరు, ఇది మీ తప్పు కాదు!"
        ),
        "woman": (
            "Your safety and well-being are paramount. If you are facing immediate danger, threat, or harm, please take immediate action to protect yourself.\n\n"
            "మీ రక్షణ మరియు భద్రత అత్యంత ముఖ్యం.\n\n"
            "Immediate Steps / తక్షణ చర్యలు:\n"
            "1. Move to a safe area or lock yourself in a safe room.\n"
            "2. Call Emergency Helpline Services at **112 / 911** immediately.\n"
            "3. Women's Helpline (India): **181** | National Emergency: **112**.\n"
            "4. Reach out to trusted friends, family, or emergency personnel right now.\n\n"
            "Please seek help right away from official support services."
        ),
        "general": (
            "If you or someone else is in immediate danger, harm, or crisis, please seek immediate help.\n\n"
            "Emergency Actions:\n"
            "1. Call Emergency Police/Medical Services at **112 / 911** immediately.\n"
            "2. For children / పిల్లల కోసం: Call Childline at **1098**.\n"
            "3. For women / మహిళల కోసం: Call Women Helpline at **181**.\n"
            "4. Reach out to a trusted adult, counselor, or authority figure right now."
        )
    }

    HELPLINE_SUMMARY = (
        "Child Helpline: 1098 | Women Helpline: 181 | Emergency Services: 112 / 911"
    )

    def analyze_message(self, message: str, audience: str = "general") -> Tuple[str, str, bool, Optional[str]]:
        """Analyzes a message to determine intent, risk level, flagged status, and emergency response if high risk."""
        clean_text = message.lower().strip()

        # 1. Check High Risk Emergency Triggers
        for pattern in self.HIGH_RISK_PATTERNS:
            if re.search(pattern, clean_text, re.IGNORECASE):
                audience_key = audience if audience in self.EMERGENCY_RESPONSES else "general"
                return (
                    "high_risk_emergency",
                    "HIGH_RISK",
                    True,
                    self.EMERGENCY_RESPONSES[audience_key]
                )

        # 2. Check Greetings
        if any(re.search(p, clean_text, re.IGNORECASE) for p in self.GREETING_PATTERNS):
            return ("greeting", "SAFE", False, None)

        # 3. Check Intent Categories
        if any(re.search(p, clean_text, re.IGNORECASE) for p in self.BODY_SAFETY_PATTERNS):
            return ("body_safety", "SENSITIVE", False, None)

        if any(re.search(p, clean_text, re.IGNORECASE) for p in self.STRANGER_SAFETY_PATTERNS):
            return ("stranger_safety", "SAFE", False, None)

        if any(re.search(p, clean_text, re.IGNORECASE) for p in self.BULLYING_PATTERNS):
            return ("bullying_harassment", "SENSITIVE", False, None)

        if any(re.search(p, clean_text, re.IGNORECASE) for p in self.ONLINE_SAFETY_PATTERNS):
            return ("online_safety", "SAFE", False, None)

        if any(re.search(p, clean_text, re.IGNORECASE) for p in self.UNSAFE_SITUATION_PATTERNS):
            return ("unsafe_situation", "SENSITIVE", False, None)

        # Default fallback intent
        return ("general_education", "SAFE", False, None)


# Global instance
safety_service = SafetyService()
