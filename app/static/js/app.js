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
  const langBtn = document.getElementById("langBtn");
  const langLabel = document.getElementById("langLabel");
  const micBtn = document.getElementById("micBtn");
  const modeBtns = document.querySelectorAll(".mode-btn");
  const chips = document.querySelectorAll(".chip");
  const recordingOverlay = document.getElementById("recordingOverlay");
  const recTimer = document.getElementById("recTimer");
  const stopRecBtn = document.getElementById("stopRecBtn");

  let currentAudience = "child";
  let ttsEnabled = true;
  let currentSpeechLang = "te-IN"; // Default voice language to Telugu
  let isRecording = false;
  let recInterval = null;
  let secondsRecorded = 0;

  // Session ID Management
  let sessionId = localStorage.getItem("minni_session_id");
  if (!sessionId) {
    sessionId = "session-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("minni_session_id", sessionId);
  }

  // Language Toggle (Telugu <-> English)
  if (langBtn && langLabel) {
    langBtn.addEventListener("click", (e) => {
      e.preventDefault();
      if (currentSpeechLang === "te-IN") {
        currentSpeechLang = "en-US";
        langLabel.textContent = "English";
      } else {
        currentSpeechLang = "te-IN";
        langLabel.textContent = "తెలుగు";
      }
      if (recognition) {
        recognition.lang = currentSpeechLang;
      }
    });
  }

  // Form Submit Handler
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

  // Audience selector
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
          <div class="msg-sender">Minni / మిన్ని</div>
          <div class="msg-text">Session restarted! తెలుగులో లేదా English లో ప్రశ్నించండి (Ask in Telugu or English)!</div>
        </div>
      </div>
    `;
  });

  // Speech Recognition (Telugu & English STT)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = currentSpeechLang;

    recognition.onstart = () => {
      isRecording = true;
      micBtn.classList.add("active");
      recordingOverlay.classList.remove("hidden");
      secondsRecorded = 0;
      recTimer.textContent = currentSpeechLang === "te-IN" ? "వినబడుతోంది... తెలుగులో మాట్లాడండి!" : "Listening... Speak in English!";

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
          recognition.lang = currentSpeechLang;
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
      appendMsg("Minni", "నేను మీకు సహాయం చేయడానికి ఇక్కడ ఉన్నాను. అత్యవసర పరిస్థితి ఉంటే 112 / 1098 కి కాల్ చేయండి.", false);
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

  // Helper to speak text aloud in Telugu or English
  function speakText(text) {
    if (!window.speechSynthesis) return;
    try {
      window.speechSynthesis.cancel();
      const clean = String(text || "").replace(/\*\*/g, "");
      const u = new SpeechSynthesisUtterance(clean);
      
      // Auto-detect Telugu characters
      const isTeluguText = /[\u0c00-\u0c7f]/.test(text);
      u.lang = isTeluguText ? "te-IN" : "en-US";
      u.rate = 0.95;

      window.speechSynthesis.speak(u);
    } catch (e) {
      console.warn("Speech synthesis notice:", e);
    }
  }
});
