import re
from typing import Dict, Tuple, Optional


class SafetyService:
    """Safety and Intent Classification Layer for Minni with English & Telugu Support."""

    # High Risk Emergency Patterns (English + Telugu Script + Telugish Transliteration)
    HIGH_RISK_PATTERNS = [
        # English
        r"\b(suicide|kill my\s*self|end my life|want to die|cutting my\s*self)\b",
        r"\b(someone is (hitting|beating|touching|following|chasing|abusing).*?(me|us))\b",
        r"\b(touching me|touches me|touched me).*?(inappropriately|private|secret|wrong)\b",
        r"\b(being abused|physical abuse|sexual abuse|raped|assaulted|molested)\b",
        r"\b(locked in|trapped in|kidnapped|held against my will)\b",
        r"\b(in danger|help me please|he has a weapon|gun|knife|scared right now)\b",
        # Telugu Script
        r"(సహాయం చేయండి|నన్ను కొడుతున్నారు|నన్ను తాకుతున్నారు|నన్ను వేధిస్తున్నారు|కాపాడండి|అపాయం|భయంగా ఉంది|చెడు స్పర్శ|చంపేస్తాను)",
        # Telugish Transliteration
        r"\b(sahayam|kapadandi|kodutunnaru|takutunnaru|nannu kodutunnaru|apayam|bhayamga undi)\b",
    ]

    BODY_SAFETY_PATTERNS = [
        r"\b(good touch|bad touch|uncomfortable touch|private parts|swimsuit rule)\b",
        r"\b(body boundaries|my body|touch me|inappropriate touch|personal space)\b",
        r"(మంచి స్పర్శ|చెడు స్పర్శ|శరీర భద్రత|ప్రైవేట్ భాగాలు)",
        r"\b(manchi sparsha|chedu sparsha|body safety)\b",
    ]

    STRANGER_SAFETY_PATTERNS = [
        r"\b(stranger|unknown person|someone I don't know|stranger danger)\b",
        r"\b(car ride|offered candy|follow a stranger|lost in store|lost in public)\b",
        r"(అపరిచితులు|తెలియని వ్యక్తులు|కొత్త వ్యక్తులు)",
    ]

    BULLYING_PATTERNS = [
        r"\b(bully|bullying|teasing|cyberbullying|mean kids|harass|harassment)\b",
        r"\b(calling me names|threatened me at school|making fun of me|mean to me)\b",
        r"(వేధింపులు|భయపెట్టడం|ఏడిపిస్తున్నారు)",
    ]

    ONLINE_SAFETY_PATTERNS = [
        r"\b(online|internet|social media|password|sharing photos|online friend)\b",
        r"\b(cyber|stranger online|chat room|game chat|private info online)\b",
        r"(ఇంటర్నెట్|ఆన్‌లైన్|పాస్‌వర్డ్|ఫోటోలు)",
    ]

    UNSAFE_SITUATION_PATTERNS = [
        r"\b(unsafe|scared|feeling uncomfortable|dark street|home alone)\b",
        r"\b(emergency|what to do if|lost|separated from mom|danger)\b",
        r"(అసురక్షితం|భయం|ఒంటరిగా)",
    ]

    GREETING_PATTERNS = [
        r"^(hi|hello|hey|hey minni|good morning|good afternoon|good evening|who are you|what can you do|నమస్కారం|హలో)$"
    ]

    # High Risk Predefined Emergency Responses (Bilingual Telugu + English)
    EMERGENCY_RESPONSES = {
        "child": (
            "ధైర్యంగా మాట్లాడినందుకు మిమ్మల్ని అభినందిస్తున్నాను. మీ భద్రత మాత్రమే ఇప్పుడు చాలా ముఖ్యం.\n"
            "I hear you, and your safety is the most important thing right now.\n\n"
            "🚨 వెంటనే ఈ 3 పనులు చేయండి / Immediate Steps:\n"
            "1. మీరు అపాయంలో ఉంటే, వెంటనే ప్రజలు లేదా ఉపాధ్యాయులు ఉన్న సురక్షితమైన ప్రదేశానికి వెళ్ళండి.\n"
            "2. మీరు నమ్మే పెద్దలకు (తల్లిదండ్రులు, ఉపాధ్యాయులు, పోలీసులు) వెంటనే చెప్పండి.\n"
            "3. చైల్డ్ హెల్ప్‌లైన్ ఉచిత నంబర్ **1098** లేదా అత్యవసర నంబర్ **112 / 911** కి వెంటనే ఫోన్ చేయండి.\n\n"
            "మీరు ఒంటరిగా లేరు. ఇది మీ తప్పు ఎంతమాత్రం కాదు!"
        ),
        "woman": (
            "మీ భద్రత మరియు రక్షణ అత్యంత ప్రధానమైనవి. మీరు ప్రమాదంలో ఉంటే వెంటనే సహాయం తీసుకోండి.\n"
            "Your safety and well-being are paramount.\n\n"
            "🚨 అత్యవసర సహాయక చర్యలు / Emergency Actions:\n"
            "1. సురక్షితమైన లేదా జనాభా ఉన్న ప్రాంతానికి వెళ్ళండి.\n"
            "2. అత్యవసర సహాయం కోసం **112** కి ఫోన్ చేయండి.\n"
            "3. మహిళా హెల్ప్‌లైన్: **181** | చైల్డ్ హెల్ప్‌లైన్: **1098**.\n"
            "4. మీ కుటుంబ సభ్యులకు లేదా పోలీసులకు వెంటనే సమాచారం ఇవ్వండి."
        ),
        "general": (
            "మీరు లేదా ఎవరైనా ప్రమాదంలో ఉంటే, దయచేసి వెంటనే పోలీసులకు లేదా హెల్ప్‌లైన్‌కి కాల్ చేయండి.\n\n"
            "🚨 Emergency Helplines:\n"
            "- Child Helpline / చైల్డ్ హెల్ప్‌లైన్: **1098**\n"
            "- Women Helpline / మహిళా హెల్ప్‌లైన్: **181**\n"
            "- Emergency Police / అత్యవసర సేవలు: **112 / 911**"
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
            if re.search(pattern, clean_text):
                audience_key = audience if audience in self.EMERGENCY_RESPONSES else "general"
                return (
                    "high_risk_emergency",
                    "HIGH_RISK",
                    True,
                    self.EMERGENCY_RESPONSES[audience_key]
                )

        # 2. Check Greetings
        if any(re.search(p, clean_text) for p in self.GREETING_PATTERNS):
            return ("greeting", "SAFE", False, None)

        # 3. Check Intent Categories
        if any(re.search(p, clean_text) for p in self.BODY_SAFETY_PATTERNS):
            return ("body_safety", "SENSITIVE", False, None)

        if any(re.search(p, clean_text) for p in self.STRANGER_SAFETY_PATTERNS):
            return ("stranger_safety", "SAFE", False, None)

        if any(re.search(p, clean_text) for p in self.BULLYING_PATTERNS):
            return ("bullying_harassment", "SENSITIVE", False, None)

        if any(re.search(p, clean_text) for p in self.ONLINE_SAFETY_PATTERNS):
            return ("online_safety", "SAFE", False, None)

        if any(re.search(p, clean_text) for p in self.UNSAFE_SITUATION_PATTERNS):
            return ("unsafe_situation", "SENSITIVE", False, None)

        # Default fallback intent
        return ("general_education", "SAFE", False, None)


# Global instance
safety_service = SafetyService()
