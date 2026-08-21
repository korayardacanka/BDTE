import { useState } from "react";
import Avatar from "./components/Avatar";

type Message = { role: "user" | "assistant"; text: string };

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Merhaba, ben BDTE prototipi. Backend'e bağlıyım (henüz LLM bağlı değilse stub yanıt döner)." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [audioLoadingIndex, setAudioLoadingIndex] = useState<number | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  async function sendMessage() {
    if (!input.trim()) return;
    const userMsg: Message = { role: "user", text: input };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg.text }),
      });
      const data = await res.json();
      setMessages((prev) => [...prev, { role: "assistant", text: data.reply }]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Backend'e ulaşılamadı. Backend'in çalıştığından emin ol (uvicorn)." },
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
        body: JSON.stringify({ text, language: "tr" }),
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

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-10 px-4">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl font-bold text-slate-800 mb-1">BDTE — Prototip Sohbet Arayüzü</h1>
        <p className="text-sm text-slate-500 mb-4">Chat UI ↔ FastAPI ↔ Ollama (persona) ↔ Coqui TTS</p>

        {/* Avatar */}
        <div className="flex justify-center mb-4">
          <Avatar isSpeaking={isSpeaking} />
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
                  m.role === "user"
                    ? "bg-blue-600 text-white"
                    : "bg-slate-100 text-slate-800"
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
            placeholder="Bir mesaj yaz…"
          />
          <button
            onClick={sendMessage}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            Gönder
          </button>
        </div>
      </div>
    </div>
  );
}