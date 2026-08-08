from app.services.safety_service import safety_service


def test_high_risk_emergency_classification():
    """Test high risk triggers return HIGH_RISK, flagged=True, and emergency response."""
    high_risk_inputs = [
        "Someone is hitting me right now",
        "Help me please im scared he has a weapon",
        "I want to kill myself",
        "I am trapped and locked in a room",
        "నన్ను కొడుతున్నారు రక్షించండి",
        "nannu kottutunnaru help me",
    ]
    for msg in high_risk_inputs:
        intent, risk, flagged, emergency_resp = safety_service.analyze_message(msg, audience="child")
        assert intent == "high_risk_emergency"
        assert risk == "HIGH_RISK"
        assert flagged is True
        assert emergency_resp is not None
        assert "1098" in emergency_resp


def test_telugu_body_safety_classification():
    """Test Telugu script and Teluglish body safety questions."""
    telugu_inputs = [
        "నాకు ఎవ‌రైనా చెడు తాకిడి చేస్తే ఏం చేయాలి?",
        "chedu taakidi ante enti?",
    ]
    for msg in telugu_inputs:
        intent, risk, flagged, emergency_resp = safety_service.analyze_message(msg)
        assert intent == "body_safety"
        assert risk == "SENSITIVE"
        assert flagged is False


def test_body_safety_classification():
    """Test body safety questions classification."""
    msg = "What is a bad touch?"
    intent, risk, flagged, emergency_resp = safety_service.analyze_message(msg)
    assert intent == "body_safety"
    assert risk == "SENSITIVE"
    assert flagged is False
    assert emergency_resp is None


def test_stranger_safety_classification():
    """Test stranger safety classification."""
    msg = "What should I do if a stranger offers me a car ride?"
    intent, risk, flagged, emergency_resp = safety_service.analyze_message(msg)
    assert intent == "stranger_safety"
    assert risk == "SAFE"
    assert flagged is False


def test_online_safety_classification():
    """Test online safety classification."""
    msg = "Is it okay to share my password with an online friend?"
    intent, risk, flagged, emergency_resp = safety_service.analyze_message(msg)
    assert intent == "online_safety"
    assert risk == "SAFE"
    assert flagged is False


def test_general_education_classification():
    """Test general educational inquiry classification."""
    msg = "Why do birds fly in the sky?"
    intent, risk, flagged, emergency_resp = safety_service.analyze_message(msg)
    assert intent == "general_education"
    assert risk == "SAFE"
    assert flagged is False
