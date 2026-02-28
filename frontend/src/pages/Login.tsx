import { useState } from 'react'
import { useAuth } from '../context/AuthContext'

export default function Login() {
    const { login, register, error } = useAuth()
    const [isRegister, setIsRegister] = useState(false)
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [name, setName] = useState('')
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        if (isRegister) {
            await register(email, password, name)
        } else {
            await login(email, password)
        }
        setLoading(false)
    }

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'var(--bg-primary)',
            position: 'relative',
            overflow: 'hidden',
        }}>
            {/* Animated background orbs */}
            <div style={{
                position: 'absolute', width: 400, height: 400, borderRadius: '50%',
                background: 'radial-gradient(circle, rgba(108,92,231,0.15) 0%, transparent 70%)',
                top: '-100px', left: '-100px', animation: 'orb-pulse 6s infinite',
            }} />
            <div style={{
                position: 'absolute', width: 300, height: 300, borderRadius: '50%',
                background: 'radial-gradient(circle, rgba(0,210,255,0.1) 0%, transparent 70%)',
                bottom: '-80px', right: '-80px', animation: 'orb-pulse 8s infinite',
            }} />

            <div style={{
                background: 'var(--bg-card)',
                backdropFilter: 'blur(20px)',
                border: '1px solid var(--border-glass)',
                borderRadius: 24,
                padding: 48,
                width: 420,
                position: 'relative',
                zIndex: 1,
            }}>
                {/* Logo */}
                <div style={{ textAlign: 'center', marginBottom: 32 }}>
                    <div style={{
                        width: 56, height: 56, borderRadius: 16,
                        background: 'var(--primary)', display: 'inline-grid', placeItems: 'center',
                        fontSize: 28, marginBottom: 16,
                    }}>✦</div>
                    <h1 style={{ fontSize: 32, fontWeight: 900, letterSpacing: 4 }}>AURA</h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginTop: 4 }}>
                        Autonomous Universal Reservation Assistant
                    </p>
                </div>

                {/* Tab Toggle */}
                <div style={{
                    display: 'flex', borderRadius: 8, overflow: 'hidden',
                    border: '1px solid var(--border-glass)', marginBottom: 24,
                }}>
                    <button
                        onClick={() => setIsRegister(false)}
                        style={{
                            flex: 1, padding: '10px 0', border: 'none', cursor: 'pointer',
                            background: !isRegister ? 'var(--primary)' : 'transparent',
                            color: 'white', fontWeight: 600, fontSize: 14, fontFamily: 'inherit',
                        }}
                    >Sign In</button>
                    <button
                        onClick={() => setIsRegister(true)}
                        style={{
                            flex: 1, padding: '10px 0', border: 'none', cursor: 'pointer',
                            background: isRegister ? 'var(--primary)' : 'transparent',
                            color: 'white', fontWeight: 600, fontSize: 14, fontFamily: 'inherit',
                        }}
                    >Create Account</button>
                </div>

                {/* Error */}
                {error && (
                    <div style={{
                        padding: '10px 14px', borderRadius: 8, marginBottom: 16,
                        background: 'rgba(255,71,87,0.1)', border: '1px solid var(--danger)',
                        color: 'var(--danger)', fontSize: 13,
                    }}>
                        {error}
                    </div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit}>
                    {isRegister && (
                        <div style={{ marginBottom: 16 }}>
                            <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
                                FULL NAME
                            </label>
                            <input
                                type="text" value={name} onChange={e => setName(e.target.value)}
                                placeholder="Your name"
                                style={{
                                    width: '100%', padding: '12px 16px', borderRadius: 10,
                                    background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-glass)',
                                    color: 'white', fontSize: 15, outline: 'none', fontFamily: 'inherit',
                                    transition: 'border 0.2s',
                                }}
                                onFocus={e => e.target.style.borderColor = 'var(--primary)'}
                                onBlur={e => e.target.style.borderColor = 'var(--border-glass)'}
                            />
                        </div>
                    )}

                    <div style={{ marginBottom: 16 }}>
                        <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
                            EMAIL ADDRESS
                        </label>
                        <input
                            type="email" value={email} onChange={e => setEmail(e.target.value)}
                            placeholder="you@example.com" required
                            style={{
                                width: '100%', padding: '12px 16px', borderRadius: 10,
                                background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-glass)',
                                color: 'white', fontSize: 15, outline: 'none', fontFamily: 'inherit',
                                transition: 'border 0.2s',
                            }}
                            onFocus={e => e.target.style.borderColor = 'var(--primary)'}
                            onBlur={e => e.target.style.borderColor = 'var(--border-glass)'}
                        />
                    </div>

                    <div style={{ marginBottom: 24 }}>
                        <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
                            PASSWORD
                        </label>
                        <input
                            type="password" value={password} onChange={e => setPassword(e.target.value)}
                            placeholder="Min 6 characters" required minLength={6}
                            style={{
                                width: '100%', padding: '12px 16px', borderRadius: 10,
                                background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-glass)',
                                color: 'white', fontSize: 15, outline: 'none', fontFamily: 'inherit',
                                transition: 'border 0.2s',
                            }}
                            onFocus={e => e.target.style.borderColor = 'var(--primary)'}
                            onBlur={e => e.target.style.borderColor = 'var(--border-glass)'}
                        />
                    </div>

                    <button
                        type="submit" disabled={loading}
                        style={{
                            width: '100%', padding: '14px 0', borderRadius: 12, border: 'none',
                            background: 'linear-gradient(135deg, var(--primary) 0%, #5b4cdb 100%)',
                            color: 'white', fontWeight: 700, fontSize: 16, cursor: 'pointer',
                            fontFamily: 'inherit', letterSpacing: 1,
                            opacity: loading ? 0.6 : 1, transition: 'all 0.2s',
                        }}
                    >
                        {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
                    </button>
                </form>

                {/* Footer */}
                <p style={{ textAlign: 'center', marginTop: 24, fontSize: 12, color: 'var(--text-muted)' }}>
                    Protected by end-to-end encryption
                </p>
            </div>
        </div>
    )
}
