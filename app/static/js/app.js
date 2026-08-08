document.addEventListener("DOMContentLoaded", () => {
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const typing = document.getElementById("typing");
  const emergencyBanner = document.getElementById("emergencyBanner");
  const resetBtn = document.getElementById("resetBtn");
  const ttsBtn = document.getElementById("ttsBtn");
  const micBtn = document.getElementById("micBtn");
  const modeBtns = document.querySelectorAll(".mode-btn");
  const chips = document.querySelectorAll(".chip");

  let currentAudience = "child";
  let ttsEnabled = true;

  let sessionId = localStorage.getItem("minni_session_id");
  if (!sessionId) {
    sessionId = "session-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("minni_session_id", sessionId);
  }

  // Audience selector
  modeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      modeBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentAudience = btn.getAttribute("data-audience");
    });
  });

  // TTS Toggle
  ttsBtn.addEventListener("click", () => {
    ttsEnabled = !ttsEnabled;
    ttsBtn.classList.toggle("active", ttsEnabled);
    ttsBtn.textContent = ttsEnabled ? "🔊 Voice On" : "🔇 Voice Off";
    if (!ttsEnabled) window.speechSynthesis.cancel();
  });

  // Quick Chips
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      messageInput.value = chip.getAttribute("data-prompt");
      chatForm.dispatchEvent(new Event("submit"));
    });
  });

  // Reset Session
  resetBtn.addEventListener("click", async () => {
    try {
      await fetch(`/api/chat/session/${sessionId}`, { method: "DELETE" });
    } catch (e) {}
    sessionId = "session-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("minni_session_id", sessionId);
    emergencyBanner.classList.add("hidden");
    chatMessages.innerHTML = `
      <div class="msg minni">
        <div class="msg-avatar">🌸</div>
        <div class="msg-body">
          <div class="msg-sender">Minni</div>
          <div class="msg-text">Session restarted! I am here to answer your questions about body safety, strangers, bullying, or online rules.</div>
        </div>
      </div>
    `;
  });

  // Speech Recognition (STT)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.onresult = (e) => {
      messageInput.value = e.results[0][0].transcript;
      chatForm.dispatchEvent(new Event("submit"));
    };
    micBtn.addEventListener("click", () => recognition.start());
  } else {
    micBtn.style.display = "none";
  }

  // Form Submit
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
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
      typing.classList.add("hidden");
      appendMsg("Minni", "I am having trouble connecting. If you feel unsafe, please call 112 / 1098 immediately!", false);
    }
  });

  function appendMsg(sender, text, isUser) {
    const div = document.createElement("div");
    div.className = `msg ${isUser ? "user" : "minni"}`;
    div.innerHTML = `
      <div class="msg-avatar">${isUser ? "👤" : "🌸"}</div>
      <div class="msg-body">
        <div class="msg-sender">${sender}</div>
        <div class="msg-text">${text.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>")}</div>
      </div>
    `;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function speakText(text) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const clean = text.replace(/\*\*/g, "");
    const u = new SpeechSynthesisUtterance(clean);
    u.rate = 0.95;
    window.speechSynthesis.speak(u);
  }
});
