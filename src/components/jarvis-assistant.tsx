import { useEffect, useRef, useState, useCallback } from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { Mic, MicOff, Volume2, VolumeX, Sparkles } from "lucide-react";

interface JarvisAssistantProps {
  userName?: string;
}

// TypeScript doesn't include Web Speech API types by default
type SpeechRecognitionType = typeof window.webkitSpeechRecognition;
type SpeechRecognitionInstance = InstanceType<SpeechRecognitionType>;
type SpeechRecognitionEventType = Event & {
  resultIndex: number;
  results: SpeechRecognitionResultList;
};

export function JarvisAssistant({ userName = "boss" }: JarvisAssistantProps) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [hasGreeted, setHasGreeted] = useState(false);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    synthRef.current = window.speechSynthesis;
    const greetTimer = setTimeout(() => {
      if (!hasGreeted) {
        setHasGreeted(true);
        speak(`Hello ${userName}. Smart Journal is online and ready.`);
      }
    }, 1200);
    return () => clearTimeout(greetTimer);
  }, [userName, hasGreeted]);

  const speak = useCallback((text: string) => {
    if (!voiceEnabled || !synthRef.current) { setResponse(text); return; }
    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95; utterance.pitch = 0.9; utterance.volume = 1;
    const voices = synthRef.current.getVoices();
    const preferredVoice = voices.find((v) => v.name.includes("Google UK English Male") || v.name.includes("Daniel") || v.name.includes("Samantha"));
    if (preferredVoice) utterance.voice = preferredVoice;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    setResponse(text);
    synthRef.current.speak(utterance);
  }, [voiceEnabled]);

  useEffect(() => {
    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionAPI) return;
    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.onstart = () => { setIsListening(true); setTranscript(""); };
    recognition.onresult = (event: SpeechRecognitionEventType) => {
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        if (event.results[i].isFinal) final += event.results[i][0].transcript;
      }
      if (final) setTranscript(final);
    };
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);
    recognitionRef.current = recognition;
  }, []);

  const toggleListening = useCallback(() => {
    if (isListening) { recognitionRef.current?.stop(); setIsListening(false); }
    else { synthRef.current?.cancel(); setIsSpeaking(false); setResponse(""); recognitionRef.current?.start(); }
  }, [isListening]);

  useEffect(() => {
    if (!transcript || isListening) return;
    const lower = transcript.toLowerCase();
    let reply = "";
    if (lower.includes("balance") || lower.includes("cash") || lower.includes("money")) reply = `Your available cash is 8,317 Hong Kong dollars. Net position is 4,347 dollars.`;
    else if (lower.includes("spend") || lower.includes("spending")) reply = `You have spent 1,653 dollars this month. That is within your safe range.`;
    else if (lower.includes("debt") || lower.includes("credit card")) reply = `Your current credit card debt is 3,970 dollars.`;
    else if (lower.includes("transaction") || lower.includes("add")) reply = `Opening the new transaction form for you now.`;
    else if (lower.includes("advisor") || lower.includes("ai")) reply = `Navigating to the AI advisor page.`;
    else if (lower.includes("hello") || lower.includes("hi")) reply = `Hello ${userName}. How can I assist with your finances today?`;
    else reply = `I heard: "${transcript}". I can tell you about your balance, spending, or debts.`;
    const timer = setTimeout(() => speak(reply), 400);
    return () => clearTimeout(timer);
  }, [transcript, isListening, speak, userName]);

  return (
    <GlassCard className="p-6 relative overflow-visible">
      <div className="flex items-center gap-4">
        <div className="relative">
          <div className={`jarvis-orb transition-all duration-500 ${isListening ? "scale-110" : isSpeaking ? "scale-105" : "scale-100"}`}>
            <div className="absolute inset-0 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white/80" />
            </div>
          </div>
          {isListening && <div className="absolute inset-0 rounded-full border-2 border-primary animate-ping" />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-semibold text-primary">J.A.R.V.I.S.</span>
            <span className="text-xs text-muted-foreground">{isListening ? "Listening..." : isSpeaking ? "Speaking..." : "Online"}</span>
          </div>
          {isListening ? (
            <div className="flex items-end gap-[3px] h-6">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="waveform-bar" style={{ animationDelay: `${i * 0.08}s` }} />
              ))}
            </div>
          ) : response ? (
            <p className="text-sm text-foreground/90 animate-in fade-in slide-in-from-bottom-2 duration-300">{response}</p>
          ) : (
            <p className="text-sm text-muted-foreground">Say "Hello" or ask about your balance, spending, or debts.</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setVoiceEnabled(!voiceEnabled)} className="p-2 rounded-full hover:bg-secondary transition-colors" title={voiceEnabled ? "Mute voice" : "Enable voice"}>
            {voiceEnabled ? <Volume2 className="w-4 h-4 text-primary" /> : <VolumeX className="w-4 h-4 text-muted-foreground" />}
          </button>
          <button onClick={toggleListening} className={`p-3 rounded-full transition-all duration-300 ${isListening ? "bg-destructive/20 text-destructive animate-pulse" : "bg-primary/20 text-primary hover:bg-primary/30"}`} title={isListening ? "Stop listening" : "Start listening"}>
            {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>
        </div>
      </div>
      {transcript && !isListening && (
        <p className="mt-3 text-xs text-muted-foreground border-t border-border/50 pt-2">You said: "{transcript}"</p>
      )}
    </GlassCard>
  );
}
