document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const typingIndicator = document.getElementById("typingIndicator");
  const emergencyBanner = document.getElementById("emergencyBanner");
  const resetChatBtn = document.getElementById("resetChatBtn");
  const ttsToggleBtn = document.getElementById("ttsToggleBtn");
  const micBtn = document.getElementById("micBtn");
  const topicGrid = document.getElementById("topicGrid");
  const modeBtns = document.querySelectorAll(".mode-pills .mode-btn");
  const ruleModalBtn = document.getElementById("ruleModalBtn");
  const ruleModal = document.getElementById("ruleModal");
  const closeModalBtn = document.getElementById("closeModalBtn");

  // State Management
  let currentAudience = "child";
  let ttsEnabled = true;
  let isRecording = false;

  // Session Persistence
  let sessionId = localStorage.getItem("minni_session_id");
  if (!sessionId) {
    sessionId = "session-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("minni_session_id", sessionId);
  }

  // Safety Rules Modal Toggle
  if (ruleModalBtn && ruleModal && closeModalBtn) {
    ruleModalBtn.addEventListener("click", () => ruleModal.classList.remove("hidden"));
    closeModalBtn.addEventListener("click", () => ruleModal.classList.add("hidden"));
    ruleModal.addEventListener("click", (e) => {
      if (e.target === ruleModal) ruleModal.classList.add("hidden");
    });
  }

  // Mode Selection Pills
  modeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      modeBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentAudience = btn.getAttribute("data-audience");
    });
  });

  // Auto Read-Aloud Toggle
  ttsToggleBtn.addEventListener("click", () => {
    ttsEnabled = !ttsEnabled;
    if (ttsEnabled) {
      ttsToggleBtn.classList.add("active");
      ttsToggleBtn.querySelector(".btn-text").textContent = "Voice On";
    } else {
      ttsToggleBtn.classList.remove("active");
      ttsToggleBtn.querySelector(".btn-text").textContent = "Voice Off";
      window.speechSynthesis.cancel();
    }
  });

  // Speech Recognition (STT) setup
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;

  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      isRecording = true;
      micBtn.classList.add("recording");
      messageInput.placeholder = "Listening... Speak now! 🎙️";
    };

    recognition.onend = () => {
      isRecording = false;
      micBtn.classList.remove("recording");
      messageInput.placeholder = "Type your question or tap microphone to speak...";
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      messageInput.value = transcript;
      chatForm.dispatchEvent(new Event("submit"));
    };

    micBtn.addEventListener("click", () => {
      if (isRecording) {
        recognition.stop();
      } else {
        recognition.start();
      }
    });
  } else {
    micBtn.style.display = "none";
  }

  // Topic Cards Click Listener
  if (topicGrid) {
    topicGrid.addEventListener("click", (e) => {
      const card = e.target.closest(".topic-card");
      if (card) {
        const promptText = card.getAttribute("data-prompt");
        messageInput.value = promptText;
        chatForm.dispatchEvent(new Event("submit"));
      }
    });
  }

  // Delegated Click for Per-Message Audio Playback
  chatMessages.addEventListener("click", (e) => {
    if (e.target.classList.contains("speak-msg-btn")) {
      const bubble = e.target.closest(".message-bubble");
      const textContent = bubble.querySelector(".message-text").innerText;
      speakText(textContent);
    }
  });

  // Reset Chat Session Handler
  resetChatBtn.addEventListener("click", async () => {
    if (confirm("Start a new chat session with Minni?")) {
      try {
        await fetch(`/api/chat/session/${sessionId}`, { method: "DELETE" });
      } catch (err) {
        console.warn("Session reset API error:", err);
      }
      sessionId = "session-" + Math.random().toString(36).substring(2, 10);
      localStorage.setItem("minni_session_id", sessionId);

      emergencyBanner.classList.add("hidden");
      chatMessages.innerHTML = `
        <div class="message-wrapper minni-message">
          <div class="message-avatar">🌸</div>
          <div class="message-bubble">
            <div class="message-sender">Minni</div>
            <div class="message-text">
              Hi! I'm <strong>Minni</strong>, your safety buddy! 💖<br><br>
              Session restarted! I am here to answer any questions about <strong>body safety</strong>, <strong>strangers</strong>, or <strong>online safety</strong>!
            </div>
            <div class="bubble-actions">
              <button class="speak-msg-btn" title="Listen to message">🔊 Listen</button>
            </div>
            <span class="message-time">Just now</span>
          </div>
        </div>
      `;
    }
  });

  // Form Submit Handler
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const userText = messageInput.value.trim();
    if (!userText) return;

    messageInput.value = "";
    playSoftChime(440); // Soft send chime

    // Append User Message
    appendMessage({
      sender: "You",
      text: userText,
      isUser: true
    });

    showTyping(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userText,
          session_id: sessionId,
          audience: currentAudience
        })
      });

      if (!response.ok) {
        throw new Error(`Server returned HTTP ${response.status}`);
      }

      const data = await response.json();
      showTyping(false);
      playSoftChime(660); // Soft receive chime

      // Append Minni Response
      appendMessage({
        sender: "Minni",
        text: data.response,
        isUser: false,
        riskLevel: data.risk_level,
        intent: data.intent
      });

      // Handle Emergency Banner
      if (data.risk_level === "HIGH_RISK" || data.flagged) {
        emergencyBanner.classList.remove("hidden");
      }

      // Auto Read-Aloud if enabled
      if (ttsEnabled && data.response) {
        speakText(data.response);
      }

    } catch (error) {
      showTyping(false);
      console.error("Chat API Error:", error);
      appendMessage({
        sender: "Minni",
        text: "I am having trouble connecting right now, but please remember: if you ever feel unsafe or need help, tell a trusted adult or call **112 / 1098** immediately!",
        isUser: false,
        riskLevel: "HIGH_RISK"
      });
    }
  });

  // Helper: Format Markdown bold & newlines
  function formatMarkdown(text) {
    let formatted = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    formatted = formatted.replace(/\n/g, "<br>");
    return formatted;
  }

  // Helper: Append Message Bubble
  function appendMessage({ sender, text, isUser, riskLevel, intent }) {
    const wrapper = document.createElement("div");
    wrapper.className = `message-wrapper ${isUser ? "user-message" : "minni-message"}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = isUser ? "👤" : "🌸";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    const senderDiv = document.createElement("div");
    senderDiv.className = "message-sender";
    senderDiv.textContent = sender;

    const textDiv = document.createElement("div");
    textDiv.className = "message-text";

    if (!isUser && riskLevel && riskLevel !== "SAFE") {
      const badge = document.createElement("span");
      badge.className = `badge-tag ${riskLevel}`;
      badge.textContent = riskLevel === "HIGH_RISK" ? "🚨 Emergency Safety Notice" : "🛡️ Body Safety Guidance";
      textDiv.appendChild(badge);
    }

    const contentDiv = document.createElement("div");
    contentDiv.innerHTML = formatMarkdown(text);
    textDiv.appendChild(contentDiv);

    if (!isUser) {
      const actionsDiv = document.createElement("div");
      actionsDiv.className = "bubble-actions";
      actionsDiv.innerHTML = `<button class="speak-msg-btn" title="Listen to message">🔊 Listen</button>`;
      textDiv.appendChild(actionsDiv);
    }

    const timeSpan = document.createElement("span");
    timeSpan.className = "message-time";
    const now = new Date();
    timeSpan.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    bubble.appendChild(senderDiv);
    bubble.appendChild(textDiv);
    bubble.appendChild(timeSpan);

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    chatMessages.appendChild(wrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Helper: Show/Hide Typing Indicator
  function showTyping(show) {
    if (show) {
      typingIndicator.classList.remove("hidden");
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
      typingIndicator.classList.add("hidden");
    }
  }

  // Helper: Play Gentle Synthesized Audio Chime
  function playSoftChime(freq) {
    try {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) return;
      const ctx = new AudioContext();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(freq, ctx.currentTime);
      gain.gain.setValueAtTime(0.05, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.3);
    } catch (e) {
      // Audio context policy fallback
    }
  }

  // Helper: Speak Text via Web Speech API
  function speakText(rawText) {
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel(); // Stop ongoing speech

    // Clean Markdown formatting before speaking
    const cleanText = rawText.replace(/\*\*/g, "").replace(/#/g, "").replace(/\[.*?\]\(.*?\)/g, "");

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.92; // Slightly slower, reassuring pace for children
    utterance.pitch = 1.15; // Friendly warm pitch

    window.speechSynthesis.speak(utterance);
  }
});
