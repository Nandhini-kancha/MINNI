import re
from typing import Dict, Tuple, Optional


class SafetyService:
    """Safety and Intent Classification Layer for Minni.
    
    Categorizes incoming user messages, evaluates risk levels, and provides
    pre-defined safe emergency responses for high-risk situations before invoking LLMs.
    """

    # High Risk Emergency Patterns
    HIGH_RISK_PATTERNS = [
        r"\b(suicide|kill my\s*self|end my life|want to die|cutting my\s*self)\b",
        r"\b(someone is (hitting|beating|touching|following|chasing|abusing).*?(me|us))\b",
        r"\b(touching me|touches me|touched me).*?(inappropriately|private|secret|wrong)\b",
        r"\b(being abused|physical abuse|sexual abuse|raped|assaulted|molested)\b",
        r"\b(locked in|trapped in|kidnapped|held against my will)\b",
        r"\b(in danger|help me please|he has a weapon|gun|knife|scared right now)\b",
        r"\b(forced to touch|touching my private|uncomfortable touch right now)\b",
        r"\b(someone is in my room|someone broke in|stalking me)\b",
    ]

    BODY_SAFETY_PATTERNS = [
        r"\b(good touch|bad touch|uncomfortable touch|private parts|swimsuit rule)\b",
        r"\b(body boundaries|my body|touch me|inappropriate touch|personal space)\b",
        r"\b(can someone touch|is it ok if someone touches|touching)\b",
    ]

    STRANGER_SAFETY_PATTERNS = [
        r"\b(stranger|unknown person|someone I don't know|stranger danger)\b",
        r"\b(car ride|offered candy|follow a stranger|lost in store|lost in public)\b",
    ]

    BULLYING_PATTERNS = [
        r"\b(bully|bullying|teasing|cyberbullying|mean kids|harass|harassment)\b",
        r"\b(calling me names|threatened me at school|making fun of me|mean to me)\b",
    ]

    ONLINE_SAFETY_PATTERNS = [
        r"\b(online|internet|social media|password|sharing photos|online friend)\b",
        r"\b(cyber|stranger online|chat room|game chat|private info online)\b",
    ]

    UNSAFE_SITUATION_PATTERNS = [
        r"\b(unsafe|scared|feeling uncomfortable|dark street|home alone)\b",
        r"\b(emergency|what to do if|lost|separated from mom|danger)\b",
    ]

    GREETING_PATTERNS = [
        r"^(hi|hello|hey|hey minni|good morning|good afternoon|good evening|who are you|what can you do)$"
    ]

    # High Risk Predefined Emergency Responses
    EMERGENCY_RESPONSES = {
        "child": (
            "I hear you, and I want you to know that you are brave for speaking up. "
            "Your safety is the most important thing right now.\n\n"
            "Here is what you should do right now:\n"
            "1. If you are in danger, please get to a safe place immediately (near other people, a teacher, or a store staff).\n"
            "2. Tell a trusted adult (like a parent, teacher, school counselor, or police officer) right now. Secrets about safety are never okay to keep.\n"
            "3. Call Child Helpline immediately at **1098** (free) or Emergency Services at **112 / 911**.\n\n"
            "You are not alone, and it is NOT your fault!"
        ),
        "woman": (
            "Your safety and well-being are paramount. If you are facing immediate danger, threat, or harm, please take immediate action to protect yourself.\n\n"
            "Immediate Steps:\n"
            "1. Move to a safe, populated area or lock yourself in a safe room if possible.\n"
            "2. Call Emergency Helpline Services at **112 / 911** immediately.\n"
            "3. Women's Helpline (India): **181** | National Domestic Violence Hotline (US): **1-800-799-SAFE (7233)**.\n"
            "4. Reach out to trusted friends, family, or emergency personnel right now.\n\n"
            "Please seek help right away from official support services."
        ),
        "general": (
            "If you or someone else is in immediate danger, harm, or crisis, please seek immediate help.\n\n"
            "Emergency Actions:\n"
            "1. Call Emergency Police/Medical Services at **112 / 911** immediately.\n"
            "2. For children: Call Childline at **1098**.\n"
            "3. For women: Call Women's Helpline at **181**.\n"
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
