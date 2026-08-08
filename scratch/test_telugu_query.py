from app.services.safety_service import safety_service
from app.services.gemini_service import gemini_service

msg = "naku safety rules and good,bad touch gurinchi explain chey"
intent, risk, flagged, emergency_resp = safety_service.analyze_message(msg, audience="child")
print(f"MSG: '{msg}'")
print(f" -> Intent: {intent}, Risk: {risk}, Flagged: {flagged}")
resp = gemini_service.generate_response(msg, intent, session_history=[], audience="child")
print(" -> Response:\n" + resp)
