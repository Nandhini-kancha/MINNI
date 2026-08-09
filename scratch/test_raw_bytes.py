import io
import requests

# 1. Create dummy raw WAV audio stream bytes
dummy_audio_bytes = b"RIFF....WAVEfmt ....data...."

# 2. Test live deployed Vercel endpoint
url = "https://minni-six.vercel.app/api/chat/voice"
headers = {
    "Content-Type": "audio/wav",
    "X-Audience": "child"
}

print(f"Sending {len(dummy_audio_bytes)} raw voice bytes to {url}...")
try:
    response = requests.post(url, data=dummy_audio_bytes, headers=headers, timeout=15)
    print("Status Code:", response.status_code)
    print("JSON Response:", response.json())
except Exception as e:
    print("Error testing endpoint:", e)
