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
  const quickPrompts = document.getElementById("quickPrompts");
  const audiencePills = document.querySelectorAll(".audience-pills .pill-btn");

  // State Management
  let currentAudience = "child";
  let ttsEnabled = true;
  let isRecording = false;

  // Session ID persistence
  let sessionId = localStorage.getItem("minni_session_id");
  if (!sessionId) {
    sessionId = "session-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("minni_session_id", sessionId);
  }

  // Audience selector pills event listener
  audiencePills.forEach((btn) => {
    btn.addEventListener("click", () => {
      audiencePills.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentAudience = btn.getAttribute("data-audience");
    });
  });

  // Text-To-Speech (TTS) Toggle
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

  // Speech Recognition (STT) Setup
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
      messageInput.placeholder = "Listening... Speak now!";
    };

    recognition.onend = () => {
      isRecording = false;
      micBtn.classList.remove("recording");
      messageInput.placeholder = "Ask Minni anything about body safety, boundaries, or online rules...";
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

  // Quick Prompt Chips Click Handler
  quickPrompts.addEventListener("click", (e) => {
    if (e.target.classList.contains("prompt-chip")) {
      const promptText = e.target.getAttribute("data-prompt");
      messageInput.value = promptText;
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Reset Chat Session Handler
  resetChatBtn.addEventListener("click", async () => {
    if (confirm("Clear conversation history and start a new chat?")) {
      try {
        await fetch(`/api/chat/session/${sessionId}`, { method: "DELETE" });
      } catch (err) {
        console.warn("Session reset API error:", err);
      }
      // Generate new session ID
      sessionId = "session-" + Math.random().toString(36).substring(2, 10);
      localStorage.setItem("minni_session_id", sessionId);

      // Reset UI
      emergencyBanner.classList.add("hidden");
      chatMessages.innerHTML = `
        <div class="message-wrapper minni-message">
          <div class="message-avatar">🌸</div>
          <div class="message-bubble">
            <div class="message-sender">Minni</div>
            <div class="message-text">
              Hello! I am **Minni**, your friendly AI safety companion. 😊<br><br>
              Session restarted! I am here to answer your questions about **body safety**, **personal boundaries**, or **online safety**.
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
    const userText = messageInput.value.strip ? messageInput.value.strip() : messageInput.value.trim();
    if (!userText) return;

    // Clear input
    messageInput.value = "";

    // Render User Message
    appendMessage({
      sender: "You",
      text: userText,
      isUser: true
    });

    // Show Typing Indicator
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

      // Render Minni Response
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

      // Speak Response via TTS if enabled
      if (ttsEnabled && data.response) {
        speakText(data.response);
      }

    } catch (error) {
      showTyping(false);
      console.error("Chat API Error:", error);
      appendMessage({
        sender: "Minni",
        text: "I am having trouble connecting right now, but please remember: if you ever feel unsafe or need help, reach out to a trusted adult or call **112 / 1098** immediately!",
        isUser: false,
        riskLevel: "HIGH_RISK"
      });
    }
  });

  // Helper: Format Markdown bold and newlines
  function formatMarkdown(text) {
    let formatted = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    
    // Convert **bold** to <strong>bold</strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Convert line breaks to <br>
    formatted = formatted.replace(/\n/g, "<br>");
    return formatted;
  }

  // Helper: Append Message Bubble to DOM
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

    // Add Risk Tag if present for Minni
    if (!isUser && riskLevel && riskLevel !== "SAFE") {
      const badge = document.createElement("span");
      badge.className = `badge-tag ${riskLevel}`;
      badge.textContent = riskLevel === "HIGH_RISK" ? "🚨 Emergency Safety Notice" : "🛡️ Sensitive Safety Response";
      textDiv.appendChild(badge);
    }

    const contentDiv = document.createElement("div");
    contentDiv.innerHTML = formatMarkdown(text);
    textDiv.appendChild(contentDiv);

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

  // Helper: Speak text using Web Speech API
  function speakText(rawText) {
    if (!window.speechSynthesis) return;

    window.speechSynthesis.cancel(); // Stop ongoing speech

    // Clean Markdown symbols before speaking
    const cleanText = rawText.replace(/\*\*/g, "").replace(/#/g, "").replace(/\[.*?\]\(.*?\)/g, "");

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.95; // Slightly slower, gentle pace for children
    utterance.pitch = 1.1;  // Slightly warmer pitch

    window.speechSynthesis.speak(utterance);
  }
});
