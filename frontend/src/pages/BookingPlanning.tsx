import { useState, useEffect } from 'react'
import axios from 'axios'

const API = 'http://localhost:8001'

export default function BookingPlanning() {
    const [bookings, setBookings] = useState<any[]>([])
    const [itinerary, setItinerary] = useState<any>(null)
    const [destination, setDestination] = useState('Dubai')
    const [days, setDays] = useState(2)
    const [budget, setBudget] = useState(50000)
    const [loading, setLoading] = useState(false)

    useEffect(() => { loadBookings() }, [])

    const loadBookings = async () => {
        try {
            const { data } = await axios.get(`${API}/bookings`)
            setBookings(data)
        } catch { }
    }

    const generateItinerary = async () => {
        setLoading(true)
        try {
            const { data } = await axios.post(`${API}/itinerary`, { destination, days, budget })
            setItinerary(data.itinerary)
        } catch (e) { console.error(e) }
        setLoading(false)
    }

    const downloadPDF = async () => {
        try {
            const resp = await axios.post(`${API}/itinerary/pdf`, { destination, days, budget }, { responseType: 'blob' })
            const url = window.URL.createObjectURL(resp.data)
            const a = document.createElement('a')
            a.href = url; a.download = `aura_itinerary_${destination}.pdf`; a.click()
        } catch (e) { console.error(e) }
    }

    return (
        <div className="page-container">
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 28, fontWeight: 800 }}>{destination} Expedition</h1>
                    <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                        📅 {days} days | 👤 2 Adults | ₹{budget?.toLocaleString()} budget
                    </p>
                </div>
                <button className="btn btn-success btn-lg" onClick={generateItinerary} disabled={loading}>
                    {loading ? '⏳ Planning...' : '✨ Plan Trip'}
                </button>
            </div>

            {/* Config */}
            <div className="glass-card" style={{ marginBottom: 24, display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'end' }}>
                <div>
                    <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>DESTINATION</label>
                    <input value={destination} onChange={e => setDestination(e.target.value)}
                        style={{ background: 'var(--bg-card)', border: '1px solid var(--border-glass)', borderRadius: 8, padding: '8px 14px', color: 'white', fontSize: 14 }} />
                </div>
                <div>
                    <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>DAYS</label>
                    <input type="number" value={days} onChange={e => setDays(+e.target.value)} min={1} max={14}
                        style={{ background: 'var(--bg-card)', border: '1px solid var(--border-glass)', borderRadius: 8, padding: '8px 14px', color: 'white', fontSize: 14, width: 80 }} />
                </div>
                <div>
                    <label style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>BUDGET (₹)</label>
                    <input type="number" value={budget} onChange={e => setBudget(+e.target.value)}
                        style={{ background: 'var(--bg-card)', border: '1px solid var(--border-glass)', borderRadius: 8, padding: '8px 14px', color: 'white', fontSize: 14, width: 120 }} />
                </div>
            </div>

            <div className="grid-2" style={{ gridTemplateColumns: '1fr 360px' }}>
                {/* Left – Main content */}
                <div>
                    {/* Hotel Card – from itinerary */}
                    {itinerary?.hotel && (
                        <div className="glass-card hotel-card" style={{ marginBottom: 20 }}>
                            <div style={{ display: 'flex', gap: 16 }}>
                                <div style={{ width: 180, height: 140, borderRadius: 12, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', display: 'grid', placeItems: 'center', fontSize: 48 }}>🏨</div>
                                <div className="hotel-info">
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span style={{ background: 'var(--warning)', color: '#0a0a1a', padding: '2px 6px', borderRadius: 4, fontSize: 11, fontWeight: 700 }}>★ {itinerary.hotel.rating}</span>
                                    </div>
                                    <div className="hotel-name">{itinerary.hotel.name}</div>
                                    <div className="hotel-price">₹{itinerary.hotel.price_per_night}/night</div>
                                    <div className="hotel-tags">
                                        <span className="hotel-tag">Free Wifi</span>
                                        <span className="hotel-tag">Pool</span>
                                        <span className="hotel-tag">Spa</span>
                                    </div>
                                    <button className="btn btn-outline" style={{ marginTop: 12 }}>Change Selection</button>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Booking History – from API */}
                    <h3 style={{ marginBottom: 12 }}>Past Bookings</h3>
                    {bookings.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No past bookings yet. Use the dashboard to make your first booking.</p>}
                    {bookings.map((b, i) => (
                        <div key={i} className="glass-card" style={{ marginBottom: 12 }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1, color: 'var(--primary)', textTransform: 'uppercase' }}>{b.intent?.replace('_', ' ')}</span>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                    <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 4, background: b.status === 'confirmed' ? 'rgba(0,210,100,0.15)' : 'rgba(255,171,0,0.15)', color: b.status === 'confirmed' ? 'var(--success)' : 'var(--warning)', fontWeight: 600 }}>{b.status || 'pending'}</span>
                                    <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{new Date(b.created_at).toLocaleString()}</span>
                                </div>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8, marginTop: 10 }}>
                                {Object.entries(b.details || {}).map(([k, v]) => (
                                    <div key={k}>
                                        <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}</div>
                                        <div style={{ fontWeight: 600, fontSize: 14 }}>{String(v)}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Right – Itinerary Timeline */}
                <div>
                    <div className="glass-card">
                        <h3 style={{ marginBottom: 16 }}>📋 AURA Itinerary</h3>
                        {!itinerary && <p style={{ color: 'var(--text-muted)' }}>Click "Plan Trip" to generate</p>}
                        {itinerary && (
                            <div className="timeline">
                                {itinerary.timeline.map((day: any) => (
                                    <div key={day.day} className="timeline-day" style={{ position: 'relative', marginBottom: 20 }}>
                                        <div className="timeline-day-badge">D{day.day}</div>
                                        {['morning', 'afternoon', 'evening'].map(tod => {
                                            const acts = day.activities.filter((a: any) => a.time_of_day === tod)
                                            if (acts.length === 0) return null
                                            return (
                                                <div key={tod}>
                                                    <div className="timeline-section-title">{tod}</div>
                                                    {acts.map((a: any, j: number) => (
                                                        <div key={j} className="timeline-activity">
                                                            <div>
                                                                <div className="timeline-activity-name">{a.name}</div>
                                                                <div className="timeline-activity-time">{a.start_time}</div>
                                                            </div>
                                                            <div className="timeline-activity-cost">₹{a.cost}</div>
                                                        </div>
                                                    ))}
                                                </div>
                                            )
                                        })}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Budget Breakdown */}
                    {itinerary && (
                        <div className="glass-card budget-breakdown" style={{ marginTop: 16 }}>
                            <h4 style={{ marginBottom: 12 }}>BUDGET BREAKDOWN</h4>
                            {Object.entries(itinerary.budget_breakdown).map(([k, v]) => (
                                <div key={k} className="budget-row">
                                    <span>{k.charAt(0).toUpperCase() + k.slice(1)}</span>
                                    <span>₹{Number(v).toLocaleString()}</span>
                                </div>
                            ))}
                            <div className="budget-total">
                                <span>Total Estimated</span>
                                <span className="amount">₹{itinerary.total_estimated.toLocaleString()}</span>
                            </div>
                            <button className="btn btn-outline" style={{ width: '100%', marginTop: 12 }} onClick={downloadPDF}>📄 Download Quote</button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
