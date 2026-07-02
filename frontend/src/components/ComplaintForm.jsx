import { useState } from "react";
import { submitComplaint } from "../services/api";

const SLA_COLORS = {
  low: { bg: "bg-green-100", text: "text-green-700", label: "Low Risk" },
  medium: { bg: "bg-yellow-100", text: "text-yellow-700", label: "Medium Risk" },
  high: { bg: "bg-red-100", text: "text-red-700", label: "High Risk" },
};

export default function ComplaintForm() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (text.trim().length < 10) { setError("Please enter at least 10 characters"); return; }
    setError("");
    setLoading(true);
    try {
      const res = await submitComplaint({ text });
      setResult(res.data);
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Submission failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => { setText(""); setResult(null); setSubmitted(false); setError(""); };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
      <h3 className="font-semibold text-gray-800 mb-4">Submit a Complaint</h3>
      <p className="text-xs text-gray-400 mb-4">Write in Hindi or English — our AI will classify and route it automatically.</p>
      {!submitted ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          <textarea value={text} onChange={(e) => setText(e.target.value)}
            placeholder="Describe your complaint..." rows={5}
            className="w-full border border-gray-300 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary resize-none" />
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-400">{text.length}/2000</span>
            <button type="submit" disabled={loading || text.length < 10}
              className="bg-primary text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors">
              {loading ? "Classifying..." : "Submit Complaint"}
            </button>
          </div>
          {error && <p className="text-red-500 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
        </form>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-green-600 bg-green-50 px-4 py-3 rounded-xl">
            <span className="text-lg">✓</span>
            <div>
              <p className="text-sm font-medium">Complaint registered successfully</p>
              <p className="text-xs mt-0.5">ID: {result.id?.slice(0, 8)}...</p>
            </div>
          </div>
          {result.classification && (
            <div className="border border-gray-100 rounded-xl p-4 space-y-3">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">AI Classification Result</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-400 mb-1">Category</p>
                  <p className="text-sm font-medium text-gray-800 capitalize">{result.classification.category.replace(/_/g, " ")}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-400 mb-1">Routed to</p>
                  <p className="text-sm font-medium text-gray-800">{result.classification.department}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="flex justify-between mb-1">
                    <span className="text-xs text-gray-400">Urgency Score</span>
                    <span className="text-sm font-bold">{result.classification.urgency_score.toFixed(1)} / 10</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className={`h-2 rounded-full ${result.classification.urgency_score >= 7 ? "bg-red-500" : result.classification.urgency_score >= 4 ? "bg-yellow-500" : "bg-green-500"}`}
                      style={{ width: `${result.classification.urgency_score * 10}%` }} />
                  </div>
                </div>
                {result.classification.sla_risk && (
                  <span className={`text-xs px-3 py-1.5 rounded-full font-medium ${SLA_COLORS[result.classification.sla_risk]?.bg} ${SLA_COLORS[result.classification.sla_risk]?.text}`}>
                    {SLA_COLORS[result.classification.sla_risk]?.label}
                  </span>
                )}
              </div>
            </div>
          )}
          <button onClick={reset} className="w-full border border-gray-200 text-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors">
            Submit another complaint
          </button>
        </div>
      )}
    </div>
  );
}
