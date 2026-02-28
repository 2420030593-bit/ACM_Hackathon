/* ═══════════════════════════════════════════════
   AURA – Voice-First AI Concierge
   Speech Recognition + Text-to-Speech + API
   ═══════════════════════════════════════════════ */

const API_URL = window.location.origin;

// ── DOM Elements ──────────────────────────────
const micBtn = document.getElementById("mic-btn");
const micIcon = document.getElementById("mic-icon");
const stopIcon = document.getElementById("stop-icon");
const waveformRing = document.getElementById("waveform-ring");
const statusPill = document.getElementById("status-pill");
const statusLabel = document.getElementById("status-label");
const stateHeadline = document.getElementById("state-headline");
const stateSubtext = document.getElementById("state-subtext");
const transcriptBox = document.getElementById("transcript-box");
const transcriptText = document.getElementById("transcript-text");
const responseArea = document.getElementById("response-area");
const historyArea = document.getElementById("history-area");

// ── State ─────────────────────────────────────
let currentState = "idle"; // idle | listening | processing | speaking
let mediaRecorder = null;
let audioChunks = [];
let currentAudio = null; // Audio element for gTTS playback
let lastAudioB64 = null; // Last audio for replay
let pendingAutoListen = false; // Auto-listen after speaking (for follow-up questions)
let conversationHistory = [];

// ── Intent Icons ──────────────────────────────
const INTENT_ICONS = {
    taxi_booking: "🚕",
    tour_booking: "🗺️",
    restaurant_booking: "🍽️",
    hotel_booking: "🏨",
    spa_booking: "🧖",
    general_help: "👋",
};

const INTENT_LABELS = {
    taxi_booking: "Taxi Booking",
    tour_booking: "Tour Booking",
    restaurant_booking: "Restaurant Booking",
    hotel_booking: "Hotel Booking",
    spa_booking: "Spa Booking",
    general_help: "General Help",
};

// ── Speech Recognition Setup ──────────────────
function setupRecognition() {
    // Recognition superseded by offline backend STT
    console.log("Offline mode initialized. Web Speech API disabled.");
}

// ── State Machine ─────────────────────────────
function setState(newState) {
    currentState = newState;

    // Reset classes
    micBtn.classList.remove("listening", "processing", "speaking");
    statusPill.classList.remove("listening", "processing", "speaking");
    waveformRing.classList.remove("active", "listening", "speaking");

    switch (newState) {
        case "idle":
            micIcon.classList.remove("hidden");
            stopIcon.classList.add("hidden");
            statusLabel.textContent = "Ready";
            stateHeadline.textContent = "Tap the mic and speak";
            stateSubtext.textContent = "I understand any language — just talk naturally";
            break;

        case "listening":
            micBtn.classList.add("listening");
            statusPill.classList.add("listening");
            waveformRing.classList.add("active", "listening");
            micIcon.classList.add("hidden");
            stopIcon.classList.remove("hidden");
            statusLabel.textContent = "Listening...";
            stateHeadline.textContent = "I'm listening...";
            stateSubtext.textContent = "Speak naturally in any language";
            break;

        case "processing":
            micBtn.classList.add("processing");
            statusPill.classList.add("processing");
            waveformRing.classList.remove("active");
            micIcon.classList.remove("hidden");
            stopIcon.classList.add("hidden");
            statusLabel.textContent = "Processing...";
            stateHeadline.textContent = "Processing your request...";
            stateSubtext.textContent = "Detecting language · Translating · Booking";
            break;

        case "speaking":
            micBtn.classList.add("speaking");
            statusPill.classList.add("speaking");
            waveformRing.classList.add("active", "speaking");
            micIcon.classList.remove("hidden");
            stopIcon.classList.add("hidden");
            statusLabel.textContent = "Speaking...";
            stateHeadline.textContent = "AURA is responding";
            stateSubtext.textContent = "Listen to the response";
            break;
    }
}

// ── Mic Button Click ──────────────────────────
micBtn.addEventListener("click", () => {
    if (currentState === "idle") {
        startListening();
    } else if (currentState === "listening") {
        stopListening();
    } else if (currentState === "speaking") {
        // Stop currently playing audio
        stopAudio();
        setState("idle");
    }
});

let audioContext = null;
let processor = null;
let input = null;
let socket = null;
let finalTranscript = "";

async function startListening() {
    responseArea.innerHTML = "";
    transcriptBox.classList.remove("hidden");
    transcriptText.textContent = "Connecting...";
    finalTranscript = "";

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/stt`;
        socket = new WebSocket(wsUrl);

        socket.onopen = async () => {
            console.log("WebSocket connected for live STT");
            audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            if (audioContext.state === 'suspended') {
                await audioContext.resume();
            }
            input = audioContext.createMediaStreamSource(stream);
            processor = audioContext.createScriptProcessor(4096, 1, 1);

            processor.onaudioprocess = (e) => {
                const channelData = e.inputBuffer.getChannelData(0);
                const int16Buffer = new Int16Array(channelData.length);
                for (let i = 0; i < channelData.length; i++) {
                    const s = Math.max(-1, Math.min(1, channelData[i]));
                    int16Buffer[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                }
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send(int16Buffer.buffer);
                }
            };

            input.connect(processor);
            processor.connect(audioContext.destination);

            setState("listening");
            stateHeadline.textContent = "Listening...";
            stateSubtext.textContent = "Transcription is happening live!";
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.text) {
                if (data.final) {
                    finalTranscript = data.text;
                    showTranscript(finalTranscript, false);
                } else {
                    showTranscript(data.text, true);
                }
            }
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
            stopListening();
        };

    } catch (err) {
        console.error("Microphone access error:", err);
        stateHeadline.textContent = "Microphone error";
        stateSubtext.textContent = "Please ensure microphone access is granted.";
    }
}

function stopListening() {
    if (processor) {
        processor.disconnect();
        input.disconnect();
        if (audioContext) audioContext.close();
        if (socket) socket.close();

        setState("processing");
        if (finalTranscript) {
            processVoiceInput(finalTranscript);
        } else {
            setState("idle");
        }

        processor = null;
        input = null;
        audioContext = null;
        socket = null;
    }
}

// ── Show Transcript ───────────────────────────
function showTranscript(text, isInterim) {
    transcriptBox.classList.remove("hidden");

    if (isInterim) {
        transcriptText.innerHTML = `<span class="interim">${escapeHtml(text)}...</span>`;
    } else {
        transcriptText.innerHTML = `"${escapeHtml(text)}"`;
    }
}

// ── Process Voice Input ───────────────────────
async function processVoiceInput(text) {
    setState("processing");

    try {
        const response = await fetch(`${API_URL}/process`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text }),
        });

        const data = await response.json();

        if (response.ok) {
            showResponse(data);

            // Check if backend wants us to auto-listen after speaking
            pendingAutoListen = data.auto_listen === true;

            // Speak the response
            speakResponse(data);

            // Add to history
            addToHistory(data);
        } else {
            setState("idle");
            stateHeadline.textContent = "Error processing request";
            stateSubtext.textContent = data.error || "Please try again";
        }
    } catch (err) {
        console.error("API Error:", err);
        setState("idle");
        stateHeadline.textContent = "Connection error";
        stateSubtext.textContent = "Make sure the AURA backend is running";
    }
}

// ── Show Response Card ────────────────────────
function showResponse(data) {
    responseArea.innerHTML = "";

    const card = document.createElement("div");
    card.className = "response-card";

    // Pipeline strip
    const pipelineHtml = `
        <div class="pipeline-strip">
            <span class="pipe-step">🎤 Voice</span>
            <span class="pipe-arrow">→</span>
            <span class="pipe-step">🌐 ${escapeHtml(data.detected_language_name || data.detected_language)}</span>
            <span class="pipe-arrow">→</span>
            <span class="pipe-step">🇬🇧 English</span>
            <span class="pipe-arrow">→</span>
            <span class="pipe-step">🧠 Intent</span>
            <span class="pipe-arrow">→</span>
            <span class="pipe-step">📋 Book</span>
            <span class="pipe-arrow">→</span>
            <span class="pipe-step">🔊 Speak</span>
        </div>
    `;

    // Language badge
    const langTag = data.detected_language !== "en"
        ? `<div class="lang-tag">🌐 ${escapeHtml(data.detected_language_name)} → "${escapeHtml(data.translated_text)}"</div>`
        : `<div class="lang-tag">🌐 English</div>`;

    // Response text (translated)
    const responseTextHtml = `<div class="response-text">${escapeHtml(data.response)}</div>`;

    // Booking blocks
    let bookingsHtml = "";
    if (data.bookings && data.bookings.length > 0) {
        for (const booking of data.bookings) {
            const icon = INTENT_ICONS[booking.intent] || "📋";
            const label = INTENT_LABELS[booking.intent] || booking.intent;
            const badgeClass = booking.status === "confirmed" ? "confirmed" : "info";

            let fieldsHtml = "";
            if (booking.details && Object.keys(booking.details).length > 0) {
                const fields = Object.entries(booking.details).map(([key, val]) => `
                    <div class="booking-field">
                        <span class="booking-field-label">${escapeHtml(key.replace(/_/g, " "))}</span>
                        <span class="booking-field-value">${escapeHtml(String(val))}</span>
                    </div>
                `).join("");
                fieldsHtml = `<div class="booking-grid">${fields}</div>`;
            }

            bookingsHtml += `
                <div class="booking-block">
                    <div class="booking-header">
                        <span class="booking-title">${icon} ${escapeHtml(label)}</span>
                        <span class="booking-badge ${badgeClass}">${escapeHtml(booking.status)}</span>
                    </div>
                    ${fieldsHtml}
                </div>
            `;
        }
    }

    // Automation banner
    let automationHtml = "";
    if (data.automation_triggered) {
        const intentMap = {
            "Taxi Booking": "🚕 Opening Uber — automating your taxi booking...",
            "Restaurant Booking": "🍽️ Opening Zomato — finding restaurants for you...",
            "Hotel Booking": "🏨 Opening Booking.com — searching hotels...",
            "Tour Booking": "🗺️ Opening Google Maps — planning your tour...",
        };
        const labels = data.intents || [];
        const automationMsgs = labels
            .map(l => intentMap[l])
            .filter(Boolean)
            .join(" | ");

        if (automationMsgs) {
            automationHtml = `
                <div class="automation-banner">
                    <div class="auto-pulse"></div>
                    <span class="auto-text">${automationMsgs}</span>
                </div>
            `;
        }
    }

    // Speak again button
    const speakBtnHtml = `
        <button class="speak-again-btn" onclick="replayResponse()">
            🔊 Listen again
        </button>
    `;

    card.innerHTML = pipelineHtml + automationHtml + langTag + responseTextHtml + bookingsHtml + speakBtnHtml;
    responseArea.appendChild(card);
}

// ── Audio Playback (gTTS from backend) ────────
function speakResponse(data) {
    // Stop any ongoing audio
    stopAudio();

    if (data.audio) {
        // Play the gTTS audio from backend (base64 MP3)
        lastAudioB64 = data.audio;
        playBase64Audio(data.audio);
    } else {
        // No audio available — go straight to idle
        console.warn("No audio in response, skipping TTS.");
        setState("idle");
    }
}

function playBase64Audio(b64) {
    try {
        const audioSrc = `data:audio/mp3;base64,${b64}`;
        currentAudio = new Audio(audioSrc);

        currentAudio.onplay = () => setState("speaking");
        currentAudio.onended = () => {
            currentAudio = null;
            if (pendingAutoListen) {
                // Auto-start listening for follow-up (e.g., hotel date questions)
                pendingAutoListen = false;
                setTimeout(() => startListening(), 500);
            } else {
                setState("idle");
            }
        };
        currentAudio.onerror = (e) => {
            console.error("Audio playback error:", e);
            currentAudio = null;
            setState("idle");
        };

        currentAudio.play();
    } catch (e) {
        console.error("Failed to play audio:", e);
        setState("idle");
    }
}

function stopAudio() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        currentAudio = null;
    }
}

function replayResponse() {
    if (lastAudioB64) {
        stopAudio();
        playBase64Audio(lastAudioB64);
    }
}

// ── Conversation History ──────────────────────
function addToHistory(data) {
    const entry = {
        text: data.original_text,
        intent: (data.intents || []).join(", "),
        lang: data.detected_language_name || data.detected_language,
        icon: data.bookings && data.bookings[0]
            ? (INTENT_ICONS[data.bookings[0].intent] || "📋")
            : "👋",
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        responseData: data,
    };

    conversationHistory.unshift(entry);

    // Keep max 5
    if (conversationHistory.length > 5) {
        conversationHistory.pop();
    }

    renderHistory();
}

function renderHistory() {
    if (conversationHistory.length === 0) return;

    historyArea.innerHTML = "";

    for (let i = 0; i < conversationHistory.length; i++) {
        const entry = conversationHistory[i];
        const item = document.createElement("div");
        item.className = "history-item";
        item.innerHTML = `
            <span class="history-icon">${entry.icon}</span>
            <div class="history-content">
                <div class="history-user-text">"${escapeHtml(entry.text)}"</div>
                <div class="history-intent">${escapeHtml(entry.intent)} · ${escapeHtml(entry.lang)}</div>
            </div>
            <span class="history-time">${entry.time}</span>
        `;

        // Click to replay this response
        item.addEventListener("click", () => {
            showResponse(entry.responseData);
            speakResponse(entry.responseData);
        });

        historyArea.appendChild(item);
    }
}

// ── Helpers ───────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ── Keyboard shortcut (spacebar to toggle mic) ──
document.addEventListener("keydown", (e) => {
    if (e.code === "Space" && e.target === document.body) {
        e.preventDefault();
        micBtn.click();
    }
});

// ── Initialize ────────────────────────────────
setupRecognition();
