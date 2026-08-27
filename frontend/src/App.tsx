import { useEffect, useState } from "react";
import Avatar from "./components/Avatar";
import PersonaForm from "./components/PersonaForm";
import WeightChart from "./components/WeightChart";

type Message = { role: "user" | "assistant"; text: string };
type PersonaSummary = {
  id: number;
  subject_name: string;
  relation: string;
  gender: "female" | "male" | null;
  age_at_reference: number | null;
  consistency_ratio: number | null;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  const [personas, setPersonas] = useState<PersonaSummary[]>([]);
  const [selectedPersonaId, setSelectedPersonaId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingPersonaId, setEditingPersonaId] = useState<number | undefined>(undefined);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [audioLoadingIndex, setAudioLoadingIndex] = useState<number | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [personaWeights, setPersonaWeights] = useState<Record<string, number> | null>(null);

  async function loadPersonas(selectId?: number) {
    try {
      const res = await fetch(`${API_BASE}/api/profile/`);
      if (!res.ok) throw new Error("Failed to load list");
      const data: PersonaSummary[] = await res.json();
      setPersonas(data);
      setLoadError(null);
      if (data.length > 0) {
        setSelectedPersonaId(selectId ?? data[0].id);
      }
    } catch (e) {
      console.error("Failed to load personas:", e);
      setLoadError("Could not reach the backend. Make sure the backend (uvicorn) is running, then refresh the page.");
    }
  }

  useEffect(() => {
    loadPersonas();
  }, []);

  // Reset the chat view when the persona changes (the backend already
  // keeps history separately per persona — this is just a visual reset).
  useEffect(() => {
    const persona = personas.find((p) => p.id === selectedPersonaId);
    setMessages([
      {
        role: "assistant",
        text: persona ? `You started a conversation with ${persona.subject_name}.` : "Hello, I'm the BDTE prototype.",
      },
    ]);
  }, [selectedPersonaId]);

  // Fetch the full profile (including AHP weights) for the weight chart.
  useEffect(() => {
    if (selectedPersonaId === null) {
      setPersonaWeights(null);
      return;
    }
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/profile/${selectedPersonaId}`);
        if (!res.ok) return;
        const data = await res.json();
        setPersonaWeights(data.mcdm_weights ?? null);
      } catch (e) {
        setPersonaWeights(null);
      }
    })();
  }, [selectedPersonaId]);

  async function startNewChat() {
    if (selectedPersonaId === null) return;
    if (!confirm("Start a new chat? This will permanently clear the conversation history with this persona.")) {
      return;
    }
    try {
      await fetch(`${API_BASE}/api/chat/history/${selectedPersonaId}`, { method: "DELETE" });
      const persona = personas.find((p) => p.id === selectedPersonaId);
      setMessages([
        { role: "assistant", text: persona ? `You started a new conversation with ${persona.subject_name}.` : "New chat started." },
      ]);
    } catch (e) {
      alert("Could not reach the backend.");
    }
  }

  async function sendMessage() {
    if (!input.trim() || selectedPersonaId === null || loading) return;
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
      if (!res.ok) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: `Error: ${data.detail || "an unknown problem occurred."}` },
        ]);
        return;
      }
      setMessages((prev) => [...prev, { role: "assistant", text: data.reply }]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Could not reach the backend. Make sure it's running." },
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
        body: JSON.stringify({ text, language: "en", persona_id: selectedPersonaId }),
      });
      if (!res.ok) throw new Error("TTS request failed");
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
      console.error("Could not generate audio:", e);
      alert("Could not generate audio. Check whether the TTS model is loaded on the backend.");
    } finally {
      setAudioLoadingIndex(null);
    }
  }

  async function deletePersona(id: number) {
    const persona = personas.find((p) => p.id === id);
    if (!persona) return;
    if (personas.length <= 1) {
      alert("At least one persona must remain — you can't delete the last one.");
      return;
    }
    if (!confirm(`Permanently delete "${persona.subject_name}"? This cannot be undone.`)) {
      return;
    }
    try {
      const res = await fetch(`${API_BASE}/api/profile/${id}`, { method: "DELETE" });
      const data = await res.json();
      if (!res.ok) {
        alert(data.detail || "Could not delete.");
        return;
      }
      loadPersonas();
    } catch (e) {
      alert("Could not reach the backend.");
    }
  }

  const selectedPersona = personas.find((p) => p.id === selectedPersonaId);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-10 px-4">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl font-bold text-slate-800 mb-1">BDTE — Prototype Chat Interface</h1>
        <p className="text-sm text-slate-500 mb-4">Chat UI ↔ FastAPI ↔ Ollama (persona) ↔ Coqui TTS</p>

        {loadError && (
          <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-3 py-2 mb-4">
            {loadError}
          </div>
        )}

        {/* Persona selector */}
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
            onClick={() => selectedPersonaId && setEditingPersonaId(selectedPersonaId)}
            disabled={!selectedPersonaId}
            title="Edit selected persona"
            className="shrink-0 bg-slate-200 text-slate-700 px-3 py-2 rounded-lg text-sm hover:bg-slate-300 disabled:opacity-50"
          >
            ✏️
          </button>
          <button
            onClick={() => selectedPersonaId && deletePersona(selectedPersonaId)}
            disabled={!selectedPersonaId || personas.length <= 1}
            title="Delete selected persona"
            className="shrink-0 bg-red-100 text-red-700 px-3 py-2 rounded-lg text-sm hover:bg-red-200 disabled:opacity-50"
          >
            🗑️
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="shrink-0 bg-slate-800 text-white px-3 py-2 rounded-lg text-sm hover:bg-slate-700"
          >
            + New Persona
          </button>
        </div>

        {/* Avatar */}
        <div className="flex justify-center mb-4">
          <Avatar
            isSpeaking={isSpeaking}
            gender={selectedPersona?.gender ?? "female"}
            age={selectedPersona?.age_at_reference ?? null}
          />
        </div>

        {/* AHP weight chart for the selected persona */}
        {personaWeights && <WeightChart weights={personaWeights} />}

        <div className="flex justify-end mb-2">
          <button
            onClick={startNewChat}
            disabled={!selectedPersonaId}
            className="text-xs text-slate-500 hover:text-slate-700 underline disabled:opacity-50"
          >
            Start new chat
          </button>
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
                  title="Listen"
                  className="shrink-0 w-7 h-7 flex items-center justify-center rounded-full bg-slate-200 hover:bg-slate-300 text-slate-600 disabled:opacity-50 text-sm"
                >
                  {audioLoadingIndex === i ? "…" : "🔊"}
                </button>
              )}
            </div>
          ))}
          {loading && <div className="self-start text-slate-400 text-sm">typing…</div>}
        </div>

        <div className="flex gap-2">
          <input
            className="flex-1 border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            placeholder={selectedPersona ? `Write a message to ${selectedPersona.subject_name}…` : "Write a message…"}
            disabled={!selectedPersonaId}
          />
          <button
            onClick={sendMessage}
            disabled={!selectedPersonaId || loading}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>

      {showForm && (
        <PersonaForm
          onClose={() => setShowForm(false)}
          onSaved={(id) => {
            setShowForm(false);
            loadPersonas(id);
          }}
        />
      )}

      {editingPersonaId !== undefined && (
        <PersonaForm
          personaId={editingPersonaId}
          onClose={() => setEditingPersonaId(undefined)}
          onSaved={(id) => {
            setEditingPersonaId(undefined);
            loadPersonas(id);
          }}
        />
      )}
    </div>
  );
}