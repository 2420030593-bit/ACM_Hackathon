import { createContext, useContext, useState, useRef, useCallback, useEffect, type ReactNode } from 'react'
import axios from 'axios'

const API = 'http://localhost:8001'

interface AuraState {
    voiceState: 'idle' | 'listening' | 'processing' | 'speaking'
    transcript: string
    isInterim: boolean
    lastResponse: any
    language: string
}

interface AuraContextType extends AuraState {
    startListening: () => void
    stopListening: () => void
    processText: (text: string) => Promise<any>
    translate: (text: string, source: string, target: string) => Promise<any>
    setVoiceState: (s: AuraState['voiceState']) => void
    setTranscript: (t: string, interim?: boolean) => void
    playAudio: (b64: string) => void
    stopAudio: () => void
}

const AuraContext = createContext<AuraContextType | null>(null)

export function AuraProvider({ children }: { children: ReactNode }) {
    const [voiceState, setVoiceState] = useState<AuraState['voiceState']>('idle')
    const [transcript, setTranscriptRaw] = useState('')
    const [isInterim, setIsInterim] = useState(false)
    const [lastResponse, setLastResponse] = useState<any>(null)
    const [language, setLanguage] = useState('en')

    const audioRef = useRef<HTMLAudioElement | null>(null)
    const finalTranscriptRef = useRef('')
    const isManualStopRef = useRef(false)

    // Web Speech API Ref
    const recognitionRef = useRef<any>(null)
    // Local POST STT Refs
    const audioContextRef = useRef<AudioContext | null>(null)
    const mediaStreamRef = useRef<MediaStream | null>(null)
    const processorRef = useRef<ScriptProcessorNode | null>(null)
    const pcmChunksRef = useRef<Int16Array[]>([])

    // STT Mode Tracking
    const [sttMode, setSttMode] = useState<'web' | 'local'>('web')

    const setTranscript = useCallback((t: string, interim = false) => {
        setTranscriptRaw(t)
        setIsInterim(interim)
    }, [])

    const playAudio = useCallback((b64: string) => {
        if (!b64) return
        stopAudio()
        // Primary engine uses MP3 (gTTS fallback Uses WAV)
        // Most browsers detect the format automatically from the stream
        const audio = new Audio(`data:audio/mpeg;base64,${b64}`)
        audioRef.current = audio
        audio.onplay = () => setVoiceState('speaking')
        audio.onended = () => { audioRef.current = null; setVoiceState('idle') }
        audio.onerror = () => { audioRef.current = null; setVoiceState('idle') }
        audio.play().catch(() => setVoiceState('idle'))
    }, [])

    const stopAudio = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause()
            audioRef.current = null
        }
    }, [])

    const processText = useCallback(async (text: string) => {
        setVoiceState('processing')
        try {
            const { data } = await axios.post(`${API}/agent/process`, { text })
            setLastResponse(data)

            // Automation is now triggered directly by the backend in real-time
            // so we don't need to fire a second request from the frontend.

            if (data.audio) playAudio(data.audio)
            else setVoiceState('idle')
            return data
        } catch (e) {
            console.error('Process error:', e)
            setVoiceState('idle')
            return null
        }
    }, [playAudio])

    const translate = useCallback(async (text: string, source: string, target: string) => {
        const { data } = await axios.post(`${API}/translate`, { text, source_lang: source, target_lang: target })
        return data
    }, [])

    // ── Local Fallback HTTP POST STT Cleanup ──
    const stopLocalSTT = async () => {
        console.log('[AURA] Stopping Local PCM capture...')
        if (processorRef.current && audioContextRef.current) {
            processorRef.current.disconnect()
        }
        if (audioContextRef.current) {
            audioContextRef.current.close().catch(e => console.error(e))
            audioContextRef.current = null
        }
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(t => t.stop())
            mediaStreamRef.current = null
        }

        const chunks = pcmChunksRef.current
        if (chunks.length === 0) {
            console.log('[AURA] No local audio chunks captured. Going idle.')
            setVoiceState('idle')
            setTranscript('')
            return
        }

        setVoiceState('processing')
        setTranscript('Transcribing offline...', false)

        const totalLength = chunks.reduce((acc, chunk) => acc + chunk.length, 0)
        const combined = new Int16Array(totalLength)
        let offset = 0
        for (const chunk of chunks) {
            combined.set(chunk, offset)
            offset += chunk.length
        }

        console.log(`[AURA] Collected ${totalLength} PCM samples. Uploading for local transcription...`)

        try {
            const blob = new Blob([combined.buffer], { type: 'application/octet-stream' })
            const response = await fetch(`${API}/voice/transcribe`, {
                method: 'POST',
                body: blob,
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('aura_token')}`
                }
            })

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)

            const data = await response.json()
            const text = data.text?.trim()

            if (text) {
                console.log(`[AURA] Local Transcription result: "${text}"`)
                setTranscript(text, false)
                processText(text)
            } else {
                console.log('[AURA] No text locally transcribed. Going idle.')
                setVoiceState('idle')
                setTranscript('')
            }
        } catch (e) {
            console.error('[AURA] Local Transcription POST error:', e)
            setVoiceState('idle')
            setTranscript('Transcription failed.')
            setTimeout(() => setTranscript(''), 2000)
        } finally {
            pcmChunksRef.current = []
        }
    }

    // ── Local STT Startup ──
    const startLocalSTT = async () => {
        console.log('[AURA] Starting Local STT Fallback')
        setSttMode('local')
        setTranscript('Connecting Offline Mic...', true)
        setVoiceState('listening')
        pcmChunksRef.current = []

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true }
            })

            if (isManualStopRef.current) {
                stream.getTracks().forEach(t => t.stop())
                return
            }

            mediaStreamRef.current = stream
            const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
            const context = new AudioContextClass({ sampleRate: 16000 })
            audioContextRef.current = context

            const source = context.createMediaStreamSource(stream)
            const processor = context.createScriptProcessor(4096, 1, 1)
            processorRef.current = processor

            source.connect(processor)
            processor.connect(context.destination)

            setTranscript('Listening (Offline)...', true)

            processor.onaudioprocess = (e) => {
                if (isManualStopRef.current) return;
                const inputData = e.inputBuffer.getChannelData(0)
                const buffer = new Int16Array(inputData.length)
                for (let i = 0; i < inputData.length; i++) {
                    let s = Math.max(-1, Math.min(1, inputData[i]))
                    buffer[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
                }
                pcmChunksRef.current.push(buffer)
            }

        } catch (err) {
            console.error('[AURA] Mic access denied for local STT:', err)
            setVoiceState('idle')
            setTranscript('')
            alert('Microphone access denied or audio device error occurred.')
        }
    }

    // ── Universal Stop ──
    const stopListening = useCallback(() => {
        console.log('[AURA] User clicked stop.')
        isManualStopRef.current = true

        if (sttMode === 'web') {
            if (recognitionRef.current) {
                recognitionRef.current.stop()
            }
            // If we have some final transcript from web API, process it
            const text = finalTranscriptRef.current.trim()
            if (text && text !== 'Listening (Web)...') {
                processText(text)
            } else {
                setVoiceState('idle')
            }
        } else {
            // Local mode
            stopLocalSTT()
        }
    }, [sttMode, processText])

    // ── Universal Start ──
    const startListening = useCallback(async () => {
        console.log('[AURA] startListening called')
        try { stopListening() } catch (e) { }

        finalTranscriptRef.current = ''
        isManualStopRef.current = false
        setVoiceState('listening')

        // Attempt Web Speech API first
        const SpeechRecognition = window.SpeechRecognition || (window as any).webkitSpeechRecognition

        if (SpeechRecognition && navigator.onLine) {
            console.log('[AURA] Initializing Web Speech API...')
            setSttMode('web')
            const recognition = new SpeechRecognition()
            recognition.continuous = true
            recognition.interimResults = true
            recognition.lang = 'en-US'
            recognitionRef.current = recognition

            recognition.onstart = () => {
                if (isManualStopRef.current) return recognition.stop()
                setTranscript('Listening (Web)...', true)
                console.log('[AURA] Web Speech API Listening...')
            }

            recognition.onresult = (e: any) => {
                let interim = ''
                let final = ''

                for (let i = e.resultIndex; i < e.results.length; ++i) {
                    if (e.results[i].isFinal) {
                        final += e.results[i][0].transcript
                    } else {
                        interim += e.results[i][0].transcript
                    }
                }

                if (final) {
                    const previous = finalTranscriptRef.current
                    const combined = previous ? previous + ' ' + final : final
                    finalTranscriptRef.current = combined
                    setTranscript(combined, false)
                } else if (interim) {
                    const previous = finalTranscriptRef.current
                    const combined = previous ? previous + ' ' + interim : interim
                    setTranscript(combined, true)
                }
            }

            recognition.onerror = (e: any) => {
                console.error('[AURA] Web Speech Error:', e.error)
                // If it's a network error or API failure, completely fallback to local offline!
                if (e.error === 'network' || !navigator.onLine) {
                    console.warn('[AURA] Network offline/error detected. Falling back to Local STT.')
                    recognition.stop()
                    startLocalSTT()
                } else if (e.error === 'no-speech') {
                    // Just ignore no speech, we auto restart loop below
                }
            }

            recognition.onend = () => {
                if (isManualStopRef.current || sttMode === 'local') return
                // Keep it alive if it just timed out
                if (voiceState === 'listening') {
                    console.log('[AURA] Web Speech API ended. Restarting loop to stay alive...')
                    try { recognition.start() } catch (err) { }
                }
            }

            try {
                recognition.start()
            } catch (e) {
                console.error('[AURA] Failed to start Web Speech API, falling back...', e)
                startLocalSTT()
            }

        } else {
            // No Web API or Browser is completely Offline -> Immediate local STT
            console.warn('[AURA] Offline or Web Speech unsupported. Using Local STT.')
            startLocalSTT()
        }

    }, [stopListening, setTranscript])

    useEffect(() => {
        return () => {
            isManualStopRef.current = true
            if (recognitionRef.current) {
                try { recognitionRef.current.stop() } catch { }
            }
            if (audioContextRef.current) {
                try { audioContextRef.current.close() } catch { }
            }
        }
    }, [])

    return (
        <AuraContext.Provider value={{
            voiceState, transcript, isInterim, lastResponse, language,
            startListening, stopListening, processText, translate,
            setVoiceState, setTranscript, playAudio, stopAudio,
        }}>
            {children}
        </AuraContext.Provider>
    )
}

export const useAura = () => {
    const ctx = useContext(AuraContext)
    if (!ctx) throw new Error('useAura must be used within AuraProvider')
    return ctx
}
