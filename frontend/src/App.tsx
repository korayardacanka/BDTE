import { useEffect, useState } from "react";
import Avatar from "./components/Avatar";
import PersonaForm from "./components/PersonaForm";

type Message = { role: "user" | "assistant"; text: string };
type PersonaSummary = {
  id: number;
  subject_name: string;
  relation: string;
  gender: "kadın" | "erkek" | null;
  age_at_reference: number | null;
  consistency_ratio: number | null;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  const [personas, setPersonas] = useState<PersonaSummary[]>([]);
  const [selectedPersonaId, setSelectedPersonaId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [audioLoadingIndex, setAudioLoadingIndex] = useState<number | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  async function loadPersonas(selectId?: number) {
    try {
      const res = await fetch(`${API_BASE}/api/profile/`);
      const data: PersonaSummary[] = await res.json();
      setPersonas(data);
      if (data.length > 0) {
        setSelectedPersonaId(selectId ?? data[0].id);
      }
    } catch (e) {
      console.error("Personalar yüklenemedi:", e);
    }
  }

  useEffect(() => {
    loadPersonas();
  }, []);

  // Persona değiştiğinde sohbet ekranını sıfırla (backend'deki geçmiş
  // persona bazında ayrı ayrı zaten korunuyor, bu sadece görsel sıfırlama).
  useEffect(() => {
    const persona = personas.find((p) => p.id === selectedPersonaId);
    setMessages([
      {
        role: "assistant",
        text: persona
          ? `${persona.subject_name} ile sohbete başladın.`
          : "Merhaba, ben BDTE prototipi.",
      },
    ]);
  }, [selectedPersonaId]);

  async function sendMessage() {
    if (!input.trim() || selectedPersonaId === null) return;
    const userMsg: Message = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.text, persona_id: selectedPersonaId }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.reply }]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Backend'e ulaşılamadı. Backend'in çalıştığından emin ol." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function playAudio(text: string, index: number) {
    setAudioLoadingIndex(index);
    try {
      const res = await fetch(`${API_BASE}/api/tts/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language: "tr", persona_id: selectedPersonaId }),
      });
      if (!res.ok) throw new Error("TTS isteği başarısız");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onplay = () => setIsSpeaking(true);
      audio.onended = () => {
        setIsSpeaking(false);
        URL.revokeObjectURL(url);
      };
      audio.onpause = () => setIsSpeaking(false);
      await audio.play();
    } catch (e) {
      console.error("Ses üretilemedi:", e);
      alert("Ses üretilemedi. Backend'de TTS modeli kurulu/yüklü mü kontrol et.");
    } finally {
      setAudioLoadingIndex(null);
    }
  }

  const selectedPersona = personas.find((p) => p.id === selectedPersonaId);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-10 px-4">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl font-bold text-slate-800 mb-1">BDTE — Prototip Sohbet Arayüzü</h1>
        <p className="text-sm text-slate-500 mb-4">Chat UI ↔ FastAPI ↔ Ollama (persona) ↔ Coqui TTS</p>

        {/* Persona seçimi */}
        <div className="flex items-center gap-2 mb-4">
          <select
            className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm bg-white"
            value={selectedPersonaId ?? ""}
            onChange={(e) => setSelectedPersonaId(parseInt(e.target.value, 10))}
          >
            {personas.map((p) => (
              <option key={p.id} value={p.id}>
                {p.subject_name} ({p.relation}{p.age_at_reference ? `, ${p.age_at_reference}` : ""})
                {p.consistency_ratio != null ? ` — CR: ${p.consistency_ratio.toFixed(3)}` : ""}
              </option>
            ))}
          </select>
          <button
            onClick={() => setShowForm(true)}
            className="shrink-0 bg-slate-800 text-white px-3 py-2 rounded-lg text-sm hover:bg-slate-700"
          >
            + Yeni Persona
          </button>
        </div>

        {/* Avatar */}
        <div className="flex justify-center mb-4">
          <Avatar
            isSpeaking={isSpeaking}
            gender={selectedPersona?.gender ?? "kadın"}
            age={selectedPersona?.age_at_reference ?? null}
          />
        </div>

        <div className="bg-white rounded-lg shadow p-4 h-96 overflow-y-auto flex flex-col gap-3 mb-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex items-end gap-2 max-w-[85%] ${
                m.role === "user" ? "self-end flex-row-reverse" : "self-start"
              }`}
            >
              <div
                className={`px-3 py-2 rounded-lg text-sm ${
                  m.role === "user" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-800"
                }`}
              >
                {m.text}
              </div>
              {m.role === "assistant" && (
                <button
                  onClick={() => playAudio(m.text, i)}
                  disabled={audioLoadingIndex === i}
                  title="Sesli dinle"
                  className="shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-slate-200 hover:bg-slate-300 text-slate-600 disabled:opacity-50 text-sm"
                >
                  {audioLoadingIndex === i ? "…" : "🔊"}
                </button>
              )}
            </div>
          ))}
          {loading && <div className="self-start text-slate-400 text-sm">yazıyor…</div>}
        </div>

        <div className="flex gap-2">
          <input
            className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder={selectedPersona ? `${selectedPersona.subject_name}'ye bir mesaj yaz…` : "Bir mesaj yaz…"}
            disabled={!selectedPersonaId}
          />
          <button
            onClick={sendMessage}
            disabled={!selectedPersonaId}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            Gönder
          </button>
        </div>
      </div>

      {showForm && (
        <PersonaForm
          onClose={() => setShowForm(false)}
          onCreated={(id) => {
            setShowForm(false);
            loadPersonas(id);
          }}
        />
      )}
    </div>
  );
}
