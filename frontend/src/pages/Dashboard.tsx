import { useState } from 'react'
import { useAura } from '../context/AuraContext'

export default function Dashboard() {
    const { voiceState, transcript, isInterim, lastResponse, startListening, stopListening, processText } = useAura()
    const [textInput, setTextInput] = useState('')

    const handleMicClick = () => {
        if (voiceState === 'listening') stopListening()
        else startListening()
    }

    const handleTextSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (textInput.trim()) {
            processText(textInput.trim())
            setTextInput('')
        }
    }

    const stateLabels: Record<string, string> = {
        idle: 'AURA is Ready',
        listening: 'AURA is Listening',
        processing: 'AURA is Thinking...',
        speaking: 'AURA is Speaking',
    }

    return (
        <div className="page-container" style={{ paddingBottom: 100 }}>
            <div className="grid-2" style={{ gridTemplateColumns: '280px 1fr 380px', alignItems: 'start' }}>
                {/* Left – Voice Orb */}
                <div className="voice-orb-container">
                    <div className={`voice-orb ${voiceState}`} onClick={handleMicClick}>
                        <span className="voice-orb-icon">
                            {voiceState === 'listening' ? '🎤' : voiceState === 'processing' ? '⏳' : voiceState === 'speaking' ? '🔊' : '🎤'}
                        </span>
                    </div>
                    <div className="voice-state-text">
                        <div className="voice-state-title">{stateLabels[voiceState]}</div>
                        <div className="voice-state-sub">
                            {transcript && <span>"{isInterim ? transcript + '...' : transcript}"</span>}
                        </div>
                    </div>
                    <div className="voice-states">
                        <div className={`voice-state-item ${voiceState === 'listening' ? 'active' : ''}`}>
                            <span>⚡</span> Listening
                        </div>
                        <div className={`voice-state-item ${voiceState === 'processing' ? 'active' : ''}`}>
                            <span>🧠</span> Thinking
                        </div>
                        <div className={`voice-state-item ${voiceState === 'speaking' ? 'active' : ''}`}>
                            <span>⚙️</span> Executing
                        </div>
                    </div>
                </div>

                {/* Center – Pipeline + Response */}
                <div>
                    {lastResponse && (
                        <>
                            {/* Response Text */}
                            <div className="glass-card">
                                <div className="transcript-label">AURA's Response</div>
                                <div className="transcript-text">{lastResponse.response}</div>
                            </div>

                            {/* Log Panel */}
                            <div className="log-panel" style={{ marginTop: 16 }}>
                                <div className="log-entry">
                                    <span className="time">[{new Date().toLocaleTimeString()}]</span> INPUT: "{lastResponse.original_text}"
                                </div>
                                <div className="log-entry">
                                    <span className="time">[{new Date().toLocaleTimeString()}]</span> LANG: {lastResponse.detected_language_name}
                                </div>
                                <div className="log-entry success">
                                    <span className="time">[{new Date().toLocaleTimeString()}]</span> INTENT: {lastResponse.intent} ({lastResponse.source})
                                </div>
                            </div>
                        </>
                    )}

                    {!lastResponse && (
                        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-muted)' }}>
                            <div style={{ fontSize: 48, marginBottom: 16 }}>🎤</div>
                            <h2>Click the orb to start speaking</h2>
                            <p>Or type a command below</p>
                        </div>
                    )}
                </div>

                {/* Right – Browser Preview placeholder */}
                <div className="glass-card" style={{ minHeight: 400, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ fontSize: 32, marginBottom: 12 }}>🌐</div>
                    <p>Browser Preview</p>
                    <p style={{ fontSize: 12 }}>Automation view will appear here</p>
                </div>
            </div>

            {/* Command Bar */}
            <form className="command-bar" onSubmit={handleTextSubmit}>
                <span style={{ fontSize: 20 }}>🎤</span>
                <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)' }}>MODE<br />Voice Command</span>
                <input
                    className="command-input"
                    placeholder="Type a new command for AURA..."
                    value={textInput}
                    onChange={e => setTextInput(e.target.value)}
                />
                <button type="submit" className="command-send">▶</button>
            </form>
        </div>
    )
}
