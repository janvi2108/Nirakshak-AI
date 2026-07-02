import { useState } from "react";
import { extractDocument } from "../services/api";

export default function DocumentExtractor({ documentId }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runExtraction = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await extractDocument(documentId);
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Extraction failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-3 border border-gray-100 rounded-xl p-4 bg-gray-50">
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-medium text-gray-700">Document Intelligence</span>
        <button onClick={runExtraction} disabled={loading}
          className="text-xs bg-primary text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {loading ? "Extracting..." : "Extract Fields"}
        </button>
      </div>
      {error && <p className="text-red-500 text-xs bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
      {result && (
        <div className="space-y-3">
          <div className="flex gap-2">
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${result.confidence_score > 0.7 ? "bg-green-100 text-green-700" : result.confidence_score > 0.4 ? "bg-yellow-100 text-yellow-700" : "bg-red-100 text-red-700"}`}>
              OCR: {(result.confidence_score * 100).toFixed(0)}% confidence
            </span>
            <span className={`text-xs px-2 py-1 rounded-full font-medium ${result.tamper_detected ? "bg-red-100 text-red-700" : "bg-green-100 text-green-700"}`}>
              {result.tamper_detected ? "⚠ Tamper Detected" : "✓ No Tampering"}
            </span>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Extracted Fields</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(result.extracted_fields)
                .filter(([k]) => !["field_confidence", "overall_confidence", "doc_type"].includes(k))
                .map(([key, value]) => (
                  <div key={key} className="bg-white rounded-lg p-2 border border-gray-100">
                    <p className="text-xs text-gray-400 capitalize">{key.replace(/_/g, " ")}</p>
                    <p className="text-sm font-medium text-gray-800 mt-0.5 truncate">
                      {value || <span className="text-gray-300 font-normal">not found</span>}
                    </p>
                  </div>
                ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
