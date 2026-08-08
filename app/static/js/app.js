document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const typing = document.getElementById("typing");
  const emergencyBanner = document.getElementById("emergencyBanner");
  const resetBtn = document.getElementById("resetBtn");
  const ttsBtn = document.getElementById("ttsBtn");
  const micBtn = document.getElementById("micBtn");
  const modeBtns = document.querySelectorAll(".mode-btn");
  const chips = document.querySelectorAll(".chip");
  const recordingOverlay = document.getElementById("recordingOverlay");
  const recTimer = document.getElementById("recTimer");
  const stopRecBtn = document.getElementById("stopRecBtn");

  let currentAudience = "child";
  let ttsEnabled = true;
  let isRecording = false;
  let recInterval = null;
  let secondsRecorded = 0;

  // Session ID Management
  let sessionId = localStorage.getItem("minni_session_id");
  if (!sessionId) {
    sessionId = "session-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("minni_session_id", sessionId);
  }

  // Prevent any form submission page reloads
  if (chatForm) {
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      e.stopPropagation();
      handleSendMessage();
      return false;
    });
  }

  if (sendBtn) {
    sendBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      handleSendMessage();
    });
  }

  // Audience selector pills
  modeBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      modeBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentAudience = btn.getAttribute("data-audience");
    });
  });

  // TTS Toggle
  ttsBtn.addEventListener("click", (e) => {
    e.preventDefault();
    ttsEnabled = !ttsEnabled;
    ttsBtn.classList.toggle("active", ttsEnabled);
    ttsBtn.textContent = ttsEnabled ? "🔊 Voice On" : "🔇 Voice Off";
    if (!ttsEnabled) window.speechSynthesis.cancel();
  });

  // Quick Prompt Chips
  chips.forEach((chip) => {
    chip.addEventListener("click", (e) => {
      e.preventDefault();
      messageInput.value = chip.getAttribute("data-prompt");
      handleSendMessage();
    });
  });

  // Reset Session History
  resetBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      await fetch(`/api/chat/session/${sessionId}`, { method: "DELETE" });
    } catch (err) {}
    sessionId = "session-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("minni_session_id", sessionId);
    emergencyBanner.classList.add("hidden");
    chatMessages.innerHTML = `
      <div class="msg minni">
        <div class="msg-avatar">🌸</div>
        <div class="msg-body">
          <div class="msg-sender">Minni</div>
          <div class="msg-text">Session restarted! Tap 🎙️ <strong>Record Voice</strong> to speak to me!</div>
        </div>
      </div>
    `;
  });

  // Speech Recognition (Voice Recording)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isRecording = true;
      micBtn.classList.add("active");
      recordingOverlay.classList.remove("hidden");
      secondsRecorded = 0;
      recTimer.textContent = "Listening... Speak now!";

      clearInterval(recInterval);
      recInterval = setInterval(() => {
        secondsRecorded++;
        recTimer.textContent = `Listening... ${secondsRecorded}s`;
      }, 1000);
    };

    recognition.onend = () => {
      isRecording = false;
      micBtn.classList.remove("active");
      recordingOverlay.classList.add("hidden");
      clearInterval(recInterval);
    };

    recognition.onerror = (event) => {
      console.warn("Speech recognition notice:", event.error);
      isRecording = false;
      micBtn.classList.remove("active");
      recordingOverlay.classList.add("hidden");
      clearInterval(recInterval);
      if (event.error === "not-allowed") {
        alert("Microphone permission was blocked. Please allow microphone access in your browser settings to use voice recording.");
      }
    };

    recognition.onresult = (e) => {
      let resultText = "";
      for (let i = e.resultIndex; i < e.results.length; ++i) {
        resultText += e.results[i][0].transcript;
      }
      if (resultText) {
        messageInput.value = resultText;
      }
    };

    micBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (isRecording) {
        recognition.stop();
      } else {
        try {
          messageInput.value = "";
          recognition.start();
        } catch (err) {
          console.warn("Speech recognition error:", err);
        }
      }
    });

    if (stopRecBtn) {
      stopRecBtn.addEventListener("click", (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (isRecording && recognition) {
          recognition.stop();
        }
        setTimeout(() => {
          if (messageInput.value.trim()) {
            handleSendMessage();
          }
        }, 300);
      });
    }
  } else {
    micBtn.addEventListener("click", (e) => {
      e.preventDefault();
      alert("Voice recording is supported in Google Chrome, Microsoft Edge, and Safari. Please use one of these browsers for voice input!");
    });
  }

  // Send Message Logic
  async function handleSendMessage() {
    const userText = messageInput.value.trim();
    if (!userText) return;

    messageInput.value = "";
    appendMsg("You", userText, true);
    typing.classList.remove("hidden");
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userText,
          session_id: sessionId,
          audience: currentAudience
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP Error ${res.status}`);
      }

      const data = await res.json();
      typing.classList.add("hidden");

      appendMsg("Minni", data.response, false);

      if (data.risk_level === "HIGH_RISK" || data.flagged) {
        emergencyBanner.classList.remove("hidden");
      }

      if (ttsEnabled && data.response) {
        speakText(data.response);
      }
    } catch (err) {
      console.error("Chat Error:", err);
      typing.classList.add("hidden");
      appendMsg("Minni", "I am here to help you stay safe! If you ever feel in danger, please call **112 / 1098** immediately.", false);
    }
  }

  // Helper to append message bubbles
  function appendMsg(sender, text, isUser) {
    const safeText = String(text || "");
    const div = document.createElement("div");
    div.className = `msg ${isUser ? "user" : "minni"}`;
    div.innerHTML = `
      <div class="msg-avatar">${isUser ? "👤" : "🌸"}</div>
      <div class="msg-body">
        <div class="msg-sender">${sender}</div>
        <div class="msg-text">${safeText.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>")}</div>
      </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Helper to speak text aloud
  function speakText(text) {
    if (!window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      const clean = String(text || "").replace(/\*\*/g, "");
      const u = new SpeechSynthesisUtterance(clean);
      u.rate = 0.95;
      window.speechSynthesis.speak(u);
    } catch (e) {
      console.warn("Speech synthesis notice:", e);
    }
  }
});
