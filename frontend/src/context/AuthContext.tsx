import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import axios from 'axios'

const API = 'http://localhost:8001'

interface User {
    email: string
    name: string
    picture?: string
    provider: string
}

interface AuthContextType {
    user: User | null
    token: string | null
    loading: boolean
    login: (email: string, password: string) => Promise<boolean>
    register: (email: string, password: string, name: string) => Promise<boolean>
    googleLogin: (idToken: string) => Promise<boolean>
    logout: () => void
    error: string
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null)
    const [token, setToken] = useState<string | null>(localStorage.getItem('aura_token'))
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState('')

    // Set default axios auth header
    useEffect(() => {
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
            // Verify token on load
            axios.get(`${API}/auth/me`)
                .then(({ data }) => { setUser(data); setLoading(false) })
                .catch(() => { logout(); setLoading(false) })
        } else {
            delete axios.defaults.headers.common['Authorization']
            setLoading(false)
        }
    }, [token])

    const saveAuth = (t: string, u: User) => {
        localStorage.setItem('aura_token', t)
        axios.defaults.headers.common['Authorization'] = `Bearer ${t}`
        setToken(t)
        setUser(u)
        setError('')
    }

    const login = async (email: string, password: string): Promise<boolean> => {
        try {
            const { data } = await axios.post(`${API}/auth/login`, { email, password })
            saveAuth(data.token, data.user)
            return true
        } catch (e: any) {
            if (!e.response) setError('Cannot connect to server. Make sure backend is running on port 8001.')
            else setError(e.response?.data?.detail || 'Login failed')
            return false
        }
    }

    const register = async (email: string, password: string, name: string): Promise<boolean> => {
        try {
            const { data } = await axios.post(`${API}/auth/register`, { email, password, name })
            saveAuth(data.token, data.user)
            return true
        } catch (e: any) {
            if (!e.response) setError('Cannot connect to server. Make sure backend is running on port 8001.')
            else setError(e.response?.data?.detail || 'Registration failed')
            return false
        }
    }

    const googleLogin = async (idToken: string): Promise<boolean> => {
        try {
            const { data } = await axios.post(`${API}/auth/google`, { id_token: idToken })
            saveAuth(data.token, data.user)
            return true
        } catch (e: any) {
            setError(e.response?.data?.detail || 'Google login failed')
            return false
        }
    }

    const logout = () => {
        localStorage.removeItem('aura_token')
        delete axios.defaults.headers.common['Authorization']
        setToken(null)
        setUser(null)
    }

    return (
        <AuthContext.Provider value={{ user, token, loading, login, register, googleLogin, logout, error }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used within AuthProvider')
    return ctx
}
