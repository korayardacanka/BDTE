import { useState } from "react";

type Message = { role: "user" | "assistant"; text: string };

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", text: "Merhaba, ben BDTE prototipi. Backend'e bağlıyım (henüz LLM bağlı değilse stub yanıt döner)." },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

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
        { role: "assistant", text: "Backend'e ulaşılamadı. `docker compose up` çalıştığından emin ol." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center py-10 px-4">
      <div className="w-full max-w-xl">
        <h1 className="text-2xl font-bold text-slate-800 mb-1">BDTE — Prototip Sohbet Arayüzü</h1>
        <p className="text-sm text-slate-500 mb-6">Hafta 1 iskeleti: chat UI ↔ FastAPI ↔ (yakında) Ollama + RAG</p>

        <div className="bg-white rounded-lg shadow p-4 h-96 overflow-y-auto flex flex-col gap-3 mb-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[80%] px-3 py-2 rounded-lg text-sm ${
                m.role === "user"
                  ? "self-end bg-blue-600 text-white"
                  : "self-start bg-slate-100 text-slate-800"
              }`}
            >
              {m.text}
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
