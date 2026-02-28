import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'

const API = 'http://localhost:8001'

const ISO_CODES = ["AF", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG", "AR", "AM", "AW", "AU", "AT", "AZ", "BS", "BH", "BD", "BB", "BY", "BE", "BZ", "BJ", "BM", "BT", "BO", "BQ", "BA", "BW", "BV", "BR", "IO", "BN", "BG", "BF", "BI", "CV", "KH", "CM", "CA", "KY", "CF", "TD", "CL", "CN", "CX", "CC", "CO", "KM", "CD", "CG", "CK", "CR", "HR", "CU", "CW", "CY", "CZ", "CI", "DK", "DJ", "DM", "DO", "EC", "EG", "SV", "GQ", "ER", "EE", "SZ", "ET", "FK", "FO", "FJ", "FI", "FR", "GF", "PF", "TF", "GA", "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD", "GP", "GU", "GT", "GG", "GN", "GW", "GY", "HT", "HM", "VA", "HN", "HK", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IM", "IL", "IT", "JM", "JP", "JE", "JO", "KZ", "KE", "KI", "KP", "KR", "KW", "KG", "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MO", "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MQ", "MR", "MU", "YT", "MX", "FM", "MD", "MC", "MN", "ME", "MS", "MA", "MZ", "MM", "NA", "NR", "NP", "NL", "NC", "NZ", "NI", "NE", "NG", "NU", "NF", "MP", "NO", "OM", "PK", "PW", "PS", "PA", "PG", "PY", "PE", "PH", "PN", "PL", "PT", "PR", "QA", "MK", "RO", "RU", "RW", "RE", "BL", "SH", "KN", "LC", "MF", "PM", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC", "SL", "SG", "SX", "SK", "SI", "SB", "SO", "ZA", "GS", "SS", "ES", "LK", "SD", "SR", "SJ", "SE", "CH", "SY", "TW", "TJ", "TZ", "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR", "TM", "TC", "TV", "UG", "UA", "AE", "GB", "UM", "US", "UY", "UZ", "VU", "VE", "VN", "VG", "VI", "WF", "EH", "YE", "ZM", "ZW"];

export default function EmergencySettings() {
    const [tab, setTab] = useState<'neural' | 'voice' | 'safety' | 'data'>('neural')
    const [country, setCountry] = useState('jp')
    const [emergencyInfo, setEmergencyInfo] = useState<any>(null)
    const [persona, setPersona] = useState('elysia')
    const [safeMode, setSafeMode] = useState(true)
    const [continuousMemory, setContinuousMemory] = useState(false)
    const [profile, setProfile] = useState<any>({})

    const countries = useMemo(() => {
        const regionNames = new Intl.DisplayNames(['en'], { type: 'region' });
        return ISO_CODES.map(c => ({
            code: c.toLowerCase(),
            name: (() => { try { return regionNames.of(c) || c } catch { return c } })()
        })).sort((a, b) => a.name.localeCompare(b.name));
    }, []);

    const currentCountryName = useMemo(() => countries.find(c => c.code === country)?.name || 'Location', [country, countries]);

    useEffect(() => { loadEmergency() }, [country])
    useEffect(() => { loadProfile() }, [])

    const loadEmergency = async () => {
        try {
            const { data } = await axios.get(`${API}/emergency/${country}`)
            setEmergencyInfo(data)
        } catch { }
    }

    const loadProfile = async () => {
        try {
            const { data } = await axios.get(`${API}/profile`)
            setProfile(data.profile || {})
        } catch { }
    }

    const saveField = async (name: string, value: string) => {
        try {
            await axios.post(`${API}/profile`, { field_name: name, field_value: value })
            setProfile((p: any) => ({ ...p, [name]: value }))
        } catch { }
    }

    return (
        <div className="page-container">
            {/* Emergency Section */}
            <div className="grid-2" style={{ marginBottom: 32 }}>
                <div className="emergency-banner">
                    <div className="emergency-badge">● ACTIVE DISTRESS SIGNAL</div>
                    <h2 className="emergency-title">Emergency Assistance</h2>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>
                        Location services active. Nearby authorities and your primary emergency contacts have been notified of your status.
                    </p>
                    <div style={{ display: 'flex', gap: 12 }}>
                        <button className="btn btn-danger btn-lg">📞 SOS QUICK CALL</button>
                        <button className="btn btn-outline btn-lg">🌐 Live Translation</button>
                    </div>

                    {/* Emergency Numbers */}
                    <div style={{ display: 'flex', gap: 16, marginTop: 24 }}>
                        {emergencyInfo && Object.entries(emergencyInfo.emergency_numbers || {}).map(([type, num]) => (
                            <div key={type} style={{ padding: '12px 16px', borderRadius: 12, border: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', gap: 12, flex: 1 }}>
                                <span style={{ fontSize: 20 }}>
                                    {type === 'police' ? '🛡️' : type === 'medical' ? '🏥' : '🚒'}
                                </span>
                                <div>
                                    <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>{type}</div>
                                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Response: 4-6 mins</div>
                                </div>
                                <span style={{ marginLeft: 'auto', fontWeight: 700, color: 'var(--danger)' }}>Dial {String(num)}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Embassy Info + Status */}
                <div>
                    <div className="glass-card" style={{ marginBottom: 16, background: 'linear-gradient(135deg, rgba(108,92,231,0.1) 0%, rgba(0,210,255,0.1) 100%)' }}>
                        <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)' }}>CURRENT LOCATION</div>
                        <h3 style={{ fontSize: 20, marginTop: 4 }}>{currentCountryName}</h3>

                        {emergencyInfo?.embassies && Object.entries(emergencyInfo.embassies).map(([nat, info]: any) => (
                            <div key={nat} style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border-glass)', marginTop: 8 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                    <span>🏛️</span>
                                    <div>
                                        <div style={{ fontWeight: 600 }}>{info.name}</div>
                                        <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{info.phone}</div>
                                    </div>
                                </div>
                            </div>
                        ))}

                        <select value={country} onChange={e => setCountry(e.target.value)}
                            style={{ marginTop: 12, width: '100%', padding: '8px 12px', borderRadius: 8, background: 'var(--bg-card)', border: '1px solid var(--border-glass)', color: 'white', fontSize: 13 }}>
                            {countries.map(c => (
                                <option key={c.code} value={c.code}>{c.code.toUpperCase()} {c.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="glass-card">
                        <h4>📋 Status Log</h4>
                        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                            <div style={{ fontSize: 13 }}><span style={{ color: 'var(--danger)' }}>14:02</span> Emergency Mode Activated</div>
                            <div style={{ fontSize: 13 }}><span style={{ color: 'var(--danger)' }}>14:03</span> Location shared with 2 contacts</div>
                            <div style={{ fontSize: 13 }}><span style={{ color: 'var(--danger)' }}>14:05</span> Embassy database synchronized</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Settings Section */}
            <h2 style={{ marginBottom: 8 }}>System Settings</h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 20, fontSize: 14 }}>Configure AURA's operational parameters</p>

            <div className="grid-2" style={{ gridTemplateColumns: '220px 1fr' }}>
                {/* Tabs */}
                <div className="settings-tabs">
                    <button className={`settings-tab ${tab === 'neural' ? 'active' : ''}`} onClick={() => setTab('neural')}>🧠 Neural Core</button>
                    <button className={`settings-tab ${tab === 'voice' ? 'active' : ''}`} onClick={() => setTab('voice')}>👤 Voice & Audio</button>
                    <button className={`settings-tab ${tab === 'safety' ? 'active' : ''}`} onClick={() => setTab('safety')}>🛡️ Safety & Privacy</button>
                    <button className={`settings-tab ${tab === 'data' ? 'active' : ''}`} onClick={() => setTab('data')}>📊 Data Management</button>
                </div>

                {/* Settings Content */}
                <div className="glass-card">
                    {tab === 'neural' && (
                        <>
                            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: 'var(--text-muted)', marginBottom: 16 }}>VOICE & PERSONA</div>
                            <div className="persona-grid">
                                {[
                                    { id: 'elysia', name: 'Elysia', desc: 'Soft, empathetic' },
                                    { id: 'atlas', name: 'Atlas', desc: 'Direct, professional' },
                                    { id: 'nova', name: 'Nova', desc: 'Energetic, casual' },
                                ].map(p => (
                                    <div key={p.id} className={`persona-card ${persona === p.id ? 'active' : ''}`} onClick={() => setPersona(p.id)}>
                                        <div style={{ fontSize: 24, marginBottom: 8 }}>👤</div>
                                        <div className="persona-name">{p.name}</div>
                                        <div className="persona-desc">{p.desc}</div>
                                    </div>
                                ))}
                            </div>

                            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 2, color: 'var(--text-muted)', marginTop: 24, marginBottom: 12 }}>CORE AUTOMATION SPEED</div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                                <span>Response Latency</span>
                                <span style={{ color: 'var(--primary)', fontSize: 13, fontWeight: 600 }}>Fast (150ms)</span>
                            </div>
                            <input type="range" min="50" max="500" defaultValue="150" style={{ width: '100%', accentColor: 'var(--primary)' }} />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                                <span>ACCURACY PRIORITY</span>
                                <span>BALANCED</span>
                                <span>SPEED PRIORITY</span>
                            </div>
                        </>
                    )}

                    {tab === 'safety' && (
                        <>
                            <div style={{ padding: '16px', borderRadius: 12, border: '1px solid var(--border-glass)', marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>🛡️ Enhanced Safe Mode</div>
                                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Filter sensitive content and adult topics</div>
                                </div>
                                <div className={`toggle ${safeMode ? 'on' : ''}`} onClick={() => setSafeMode(!safeMode)}></div>
                            </div>
                            <div style={{ padding: '16px', borderRadius: 12, border: '1px solid var(--border-glass)', marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>🧠 Continuous Memory</div>
                                    <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>AURA learns from past interactions</div>
                                </div>
                                <div className={`toggle ${continuousMemory ? 'on' : ''}`} onClick={() => setContinuousMemory(!continuousMemory)}></div>
                            </div>
                            <button className="btn btn-danger" style={{ marginTop: 16 }}>🗑️ Reset Neural Memory (Wipe All Data)</button>
                        </>
                    )}

                    {tab === 'data' && (
                        <>
                            <h4 style={{ marginBottom: 12 }}>Profile Vault</h4>
                            {['first_name', 'last_name', 'email', 'phone', 'passport_number', 'nationality'].map(field => (
                                <div key={field} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'center' }}>
                                    <label style={{ width: 120, fontSize: 12, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{field.replace('_', ' ')}</label>
                                    <input
                                        value={profile[field] || ''}
                                        onChange={e => setProfile((p: any) => ({ ...p, [field]: e.target.value }))}
                                        onBlur={e => saveField(field, e.target.value)}
                                        style={{ flex: 1, padding: '6px 10px', borderRadius: 6, background: 'var(--bg-card)', border: '1px solid var(--border-glass)', color: 'white', fontSize: 13 }}
                                    />
                                </div>
                            ))}
                        </>
                    )}

                    {tab === 'voice' && (
                        <>
                            <h4 style={{ marginBottom: 12 }}>Audio Configuration</h4>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                                STT Engine: Vosk (Offline)<br />
                                TTS Engine: pyttsx3 (Offline)<br />
                                Sample Rate: 16kHz Mono<br />
                                LLM: Ollama ({'{model}'})
                            </p>
                        </>
                    )}
                </div>
            </div>

            {/* Footer */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 32, padding: '16px 0', borderTop: '1px solid var(--border-glass)', fontSize: 12, color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    <div className="status-dot"></div>
                    <span>SYSTEM ONLINE</span>
                    <span>|</span>
                    <span>V2.0.0-STABLE</span>
                </div>
                <div style={{ display: 'flex', gap: 16 }}>
                    <span>PRIVACY POLICY</span>
                    <span>SUPPORT</span>
                </div>
            </div>
        </div>
    )
}
