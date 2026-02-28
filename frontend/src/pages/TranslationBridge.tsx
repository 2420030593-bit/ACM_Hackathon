import { useState } from 'react'
import { useAura } from '../context/AuraContext'

const LANGUAGES = [
    { code: 'en', name: 'English (US)', flag: '🇺🇸' },
    { code: 'hi', name: 'Hindi', flag: '🇮🇳' },
    { code: 'te', name: 'Telugu', flag: '🇮🇳' },
    { code: 'ja', name: 'Japanese', flag: '🇯🇵' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
]

export default function TranslationBridge() {
    const { translate, playAudio } = useAura()
    const [sourceLang, setSourceLang] = useState('en')
    const [targetLang, setTargetLang] = useState('ja')
    const [inputText, setInputText] = useState('')
    const [translatedText, setTranslatedText] = useState('')
    const [loading, setLoading] = useState(false)
    const [voiceSynthesis, setVoiceSynthesis] = useState(true)
    const [storeHistory, setStoreHistory] = useState(false)
    const [history, setHistory] = useState<any[]>([])

    const [audioData, setAudioData] = useState<string | null>(null)

    const handleTranslate = async () => {
        if (!inputText.trim()) return
        setLoading(true)
        setAudioData(null)
        try {
            const data = await translate(inputText.trim(), sourceLang, targetLang)
            setTranslatedText(data.translated)
            if (data.audio) {
                setAudioData(data.audio)
                if (voiceSynthesis) {
                    playAudio(data.audio)
                }
            }
            if (storeHistory) {
                setHistory(prev => [{ source: inputText, translated: data.translated, time: new Date() }, ...prev.slice(0, 11)])
            }
        } catch (e) { console.error(e) }
        setLoading(false)
    }

    const handlePlayAudio = () => {
        if (audioData) {
            playAudio(audioData)
        }
    }

    const swapLangs = () => {
        setSourceLang(targetLang)
        setTargetLang(sourceLang)
        setInputText(translatedText)
        setTranslatedText('')
    }

    const sourceInfo = LANGUAGES.find(l => l.code === sourceLang) || LANGUAGES[0]
    const targetInfo = LANGUAGES.find(l => l.code === targetLang) || LANGUAGES[3]

    return (
        <div className="page-container">
            <div className="grid-2" style={{ gridTemplateColumns: '280px 1fr' }}>
                {/* Left Sidebar */}
                <div>
                    {/* Language Pair */}
                    <div className="glass-card" style={{ marginBottom: 20 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                            <h3>Language Pair</h3>
                            <span style={{ padding: '4px 10px', borderRadius: 20, background: 'rgba(108,92,231,0.2)', color: 'var(--primary)', fontSize: 10, fontWeight: 700 }}>AUTO DETECT</span>
                        </div>

                        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', marginBottom: 4 }}>PRIMARY (TOURIST)</div>
                        <select value={sourceLang} onChange={e => setSourceLang(e.target.value)}
                            style={{ width: '100%', padding: '10px 14px', borderRadius: 8, background: 'var(--bg-card)', border: '1px solid var(--border-glass)', color: 'white', fontSize: 14, marginBottom: 16 }}>
                            {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.flag} {l.name}</option>)}
                        </select>

                        <div style={{ textAlign: 'center', margin: '8px 0' }}>
                            <button onClick={swapLangs} style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--primary)', border: 'none', color: 'white', cursor: 'pointer', fontSize: 16 }}>⇅</button>
                        </div>

                        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', marginBottom: 4 }}>SECONDARY (LOCAL)</div>
                        <select value={targetLang} onChange={e => setTargetLang(e.target.value)}
                            style={{ width: '100%', padding: '10px 14px', borderRadius: 8, background: 'var(--bg-card)', border: '1px solid var(--border-glass)', color: 'white', fontSize: 14 }}>
                            {LANGUAGES.map(l => <option key={l.code} value={l.code}>{l.flag} {l.name}</option>)}
                        </select>

                        <div style={{ marginTop: 20, display: 'flex', flexDirection: 'column', gap: 12 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: 14 }}>Voice Synthesis</span>
                                <div className={`toggle ${voiceSynthesis ? 'on' : ''}`} onClick={() => setVoiceSynthesis(!voiceSynthesis)}></div>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: 14 }}>Store History</span>
                                <div className={`toggle ${storeHistory ? 'on' : ''}`} onClick={() => setStoreHistory(!storeHistory)}></div>
                            </div>
                        </div>
                    </div>


                </div>

                {/* Right – Translation Panels */}
                <div>
                    {/* Tourist Panel */}
                    <div className="translation-panel" style={{ marginBottom: 20 }}>
                        <div className="translation-label">YOU SAID:</div>
                        <span className="translation-badge badge-tourist">TOURIST</span>
                        <textarea
                            className="translation-text"
                            value={inputText}
                            onChange={e => setInputText(e.target.value)}
                            placeholder="Type or speak to translate..."
                            style={{ width: '100%', background: 'none', border: 'none', outline: 'none', color: 'white', resize: 'none', minHeight: 80, fontFamily: 'inherit' }}
                        />
                        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 16 }}>
                            <button className="btn btn-primary" onClick={handleTranslate} disabled={loading}>
                                {loading ? '⏳ Translating...' : '🌐 Translate'}
                            </button>
                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                                {inputText.length > 0 ? `${inputText.split(' ').length} words` : ''}
                            </span>
                        </div>
                    </div>

                    {/* Local Panel */}
                    <div className="translation-panel">
                        <div className="translation-label">TRANSLATED {targetInfo.name.toUpperCase()}:</div>
                        <span className="translation-badge badge-local">LOCAL</span>
                        <div className="translation-text" style={{ marginTop: 32, minHeight: 60 }}>
                            {translatedText ? `"${translatedText}"` : <span style={{ color: 'var(--text-muted)' }}>Translation will appear here...</span>}
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16 }}>
                            <button className="icon-btn" onClick={handlePlayAudio} disabled={!audioData} style={{ width: 40, height: 40, opacity: audioData ? 1 : 0.5 }}>🔊</button>
                            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{audioData ? 'READY TO PLAY' : 'STANDBY'}</span>
                        </div>
                    </div>

                    {/* Bottom Bar */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16 }}>
                        <div style={{ display: 'flex', gap: 12, alignItems: 'center', color: 'var(--text-secondary)', fontSize: 13 }}>
                            <span>🕐</span>
                            <span>Total sessions today: {history.length} translations</span>
                        </div>
                        <div style={{ display: 'flex', gap: 8 }}>
                            <button className="btn btn-outline">↓ OFFLINE MODE</button>
                            <button className="btn btn-primary">⇄ BRIDGE SESSION</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
