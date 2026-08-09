import io
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_post_chat_standalone_wake_word_greeting():
    """Test POST /api/chat with standalone 'Hey Minni' greeting."""
    payload = {
        "message": "Hey Minni",
        "audience": "child"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "greeting"
    assert "Hello" in data["response"] or "Minni" in data["response"]
    assert "voice_text" in data


def test_post_chat_normal_query():
    """Test POST /api/chat with a normal safety question."""
    payload = {
        "message": "What is good touch and bad touch?",
        "audience": "child"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "voice_text" in data
    assert len(data["voice_text"]) > 0
    assert "session_id" in data
    assert data["intent"] == "body_safety"
    assert data["risk_level"] in ["SAFE", "SENSITIVE"]
    assert data["flagged"] is False
    assert data["action_taken"] == "normal_response"


def test_post_chat_wake_word_stripping():
    """Test POST /api/chat strips 'Hey Minni' wake word prefix from robot input."""
    payload = {
        "message": "Hey Minni, explain about safe touch",
        "audience": "child"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "body_safety"
    assert "voice_text" in data


def test_post_chat_direct_raw_voice_bytes():
    """Test POST /api/chat/voice with direct raw voice audio stream bytes in request body."""
    raw_voice_bytes = b"RIFF....WAVEfmt ....data...."
    headers = {"Content-Type": "audio/wav", "X-Audience": "child"}
    
    response = client.post("/api/chat/voice", content=raw_voice_bytes, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "voice_text" in data
    assert "session_id" in data
    assert data["intent"] == "voice_audio_input"
    assert data["action_taken"] == "multimodal_audio_response"


def test_post_chat_voice_audio_upload():
    """Test POST /api/chat/voice with dummy audio file upload."""
    dummy_audio_bytes = b"RIFF....WAVEfmt ....data...."
    files = {"audio_file": ("test_audio.wav", io.BytesIO(dummy_audio_bytes), "audio/wav")}
    data_payload = {"audience": "child"}
    
    response = client.post("/api/chat/voice", files=files, data=data_payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "voice_text" in data
    assert "session_id" in data
    assert data["intent"] == "voice_audio_input"
    assert data["action_taken"] == "multimodal_audio_response"


def test_post_chat_high_risk_emergency_query():
    """Test POST /api/chat with a high-risk emergency query triggering immediate safe response."""
    payload = {
        "message": "Someone is hitting me right now help me",
        "audience": "child"
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "high_risk_emergency"
    assert data["risk_level"] == "HIGH_RISK"
    assert data["flagged"] is True
    assert data["action_taken"] == "predefined_emergency_override"
    assert "voice_text" in data
    assert "1098" in data["response"] or "112" in data["response"]
    assert data["helpline_info"] is not None


def test_post_chat_session_context_continuity():
    """Test conversation context continuity across session_id calls."""
    session_id = "test-session-999"
    payload1 = {
        "message": "My name is Sam and I want to ask about stranger safety.",
        "session_id": session_id
    }
    res1 = client.post("/api/chat", json=payload1)
    assert res1.status_code == 200
    assert res1.json()["session_id"] == session_id

    payload2 = {
        "message": "What was my question about?",
        "session_id": session_id
    }
    res2 = client.post("/api/chat", json=payload2)
    assert res2.status_code == 200
    assert res2.json()["session_id"] == session_id


def test_delete_chat_session():
    """Test DELETE /api/chat/session/{session_id} clearing session history."""
    session_id = "test-delete-session"
    client.post("/api/chat", json={"message": "Hello", "session_id": session_id})
    
    del_res = client.delete(f"/api/chat/session/{session_id}")
    assert del_res.status_code == 200
    assert del_res.json()["message"] == f"Session '{session_id}' history cleared successfully."
