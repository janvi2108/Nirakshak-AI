import { useState } from "react";
import { queryRAG } from "../services/api";

export default function ChatWidget() {
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi! Ask me about certificate requirements, processing times, or scheme eligibility." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const userMsg = { role: "user", text: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await queryRAG({ query: input, language: "en" });
      setMessages((m) => [...m, { role: "assistant", text: res.data.answer, sources: res.data.sources }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: "Sorry, I couldn't process that. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm flex flex-col h-[500px]">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-800">Citizen Assistant</h3>
        <p className="text-xs text-gray-400">RAG-powered · Hindi & English</p>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${msg.role === "user" ? "bg-primary text-white" : "bg-gray-100 text-gray-800"}`}>
              <p>{msg.text}</p>
              {msg.sources?.length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-400">
                  Sources: {msg.sources.map((s) => s.source_doc).join(", ")}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <div className="text-xs text-gray-400">Thinking...</div>}
      </div>
      <form onSubmit={sendMessage} className="p-3 border-t border-gray-100 flex gap-2">
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a question..."
          className="flex-1 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
        <button type="submit" disabled={loading} className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50">
          Send
        </button>
      </form>
    </div>
  );
}
