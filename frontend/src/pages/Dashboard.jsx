import { useState, useEffect } from "react";
import { createApplication, listApplications, uploadDocument } from "../services/api";
import { useAuth } from "../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import DocumentExtractor from "../components/DocumentExtractor";
import ComplaintForm from "../components/ComplaintForm";
import ChatWidget from "../components/ChatWidget";

const CERT_TYPES = [
  { value: "caste_certificate", label: "Caste Certificate" },
  { value: "birth_certificate", label: "Birth Certificate" },
  { value: "income_certificate", label: "Income Certificate" },
  { value: "domicile_certificate", label: "Domicile Certificate" },
  { value: "death_certificate", label: "Death Certificate" },
];

const STATUS_COLORS = {
  submitted: "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  officer_review: "bg-purple-100 text-purple-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
};

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [applications, setApplications] = useState([]);
  const [activeTab, setActiveTab] = useState("applications");
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [appForm, setAppForm] = useState({
    cert_type: "caste_certificate", citizen_name: "", citizen_phone: "",
    citizen_email: "", district: "", aadhaar_last4: "",
  });

  const [createdAppId, setCreatedAppId] = useState(null);
  const [createdDocId, setCreatedDocId] = useState(null);
  const [docFile, setDocFile] = useState(null);
  const [docType, setDocType] = useState("aadhaar");
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    if (!user) { navigate("/"); return; }
    fetchApplications();
  }, [user]);

  const fetchApplications = async () => {
    try {
      const res = await listApplications();
      setApplications(res.data);
    } catch (e) { console.error(e); }
  };

  const handleAppSubmit = async (e) => {
    e.preventDefault();
    setError(""); setSuccess("");
    setSubmitting(true);
    try {
      const res = await createApplication(appForm);
      setCreatedAppId(res.data.id);
      setSuccess(`Application created! ID: ${res.data.id}`);
      fetchApplications();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create application");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDocUpload = async (e) => {
    e.preventDefault();
    if (!docFile || !createdAppId) return;
    setUploading(true);
    const formData = new FormData();
    formData.append("application_id", createdAppId);
    formData.append("doc_type", docType);
    formData.append("file", docFile);
    try {
      const res = await uploadDocument(formData);
      setCreatedDocId(res.data.id);
      setSuccess("Document uploaded successfully!");
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const resetForm = () => {
    setShowForm(false); setCreatedAppId(null); setCreatedDocId(null);
    setDocFile(null); setError(""); setSuccess("");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center">
        <h1 className="text-lg font-bold text-gray-900">NIRAKSHAK-AI</h1>
        <button onClick={logout} className="text-sm text-gray-500 hover:text-red-500 transition-colors">Logout</button>
      </nav>

      <div className="max-w-4xl mx-auto p-6">
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-6 w-fit">
          {["applications", "complaints", "assistant"].map((tab) => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize ${activeTab === tab ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
              {tab}
            </button>
          ))}
        </div>

        {activeTab === "applications" && (
          <>
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold text-gray-800">My Applications</h2>
              <button onClick={() => showForm ? resetForm() : setShowForm(true)}
                className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                {showForm ? "Cancel" : "+ New Application"}
              </button>
            </div>

            {showForm && (
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 mb-6">
                <h3 className="font-semibold text-gray-800 mb-4">
                  {createdAppId ? "Step 2 — Upload Document" : "Step 1 — Application Details"}
                </h3>
                {!createdAppId ? (
                  <form onSubmit={handleAppSubmit} className="grid grid-cols-2 gap-4">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">Certificate Type</label>
                      <select value={appForm.cert_type} onChange={(e) => setAppForm({ ...appForm, cert_type: e.target.value })}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                        {CERT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                      </select>
                    </div>
                    {[
                      { name: "citizen_name", label: "Full Name", placeholder: "Rahul Sharma" },
                      { name: "citizen_phone", label: "Phone", placeholder: "9876543210" },
                      { name: "citizen_email", label: "Email (optional)", placeholder: "email@example.com" },
                      { name: "district", label: "District", placeholder: "Noida" },
                      { name: "aadhaar_last4", label: "Last 4 digits of Aadhaar", placeholder: "XXXX", maxLength: 4 },
                    ].map((field) => (
                      <div key={field.name} className={field.name === "aadhaar_last4" ? "col-span-2" : ""}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">{field.label}</label>
                        <input name={field.name} value={appForm[field.name]}
                          onChange={(e) => setAppForm({ ...appForm, [e.target.name]: e.target.value })}
                          placeholder={field.placeholder} maxLength={field.maxLength}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary" />
                      </div>
                    ))}
                    <div className="col-span-2">
                      <button type="submit" disabled={submitting}
                        className="w-full bg-primary text-white py-2 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50">
                        {submitting ? "Submitting..." : "Submit Application →"}
                      </button>
                    </div>
                  </form>
                ) : !createdDocId ? (
                  <form onSubmit={handleDocUpload} className="space-y-4">
                    <p className="text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">✓ Application created. Now upload your supporting document.</p>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Document Type</label>
                      <select value={docType} onChange={(e) => setDocType(e.target.value)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                        <option value="aadhaar">Aadhaar Card</option>
                        <option value="birth_cert">Birth Certificate</option>
                        <option value="caste_cert">Caste Certificate</option>
                        <option value="income_proof">Income Proof</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Upload File (JPEG, PNG, PDF — max 10MB)</label>
                      <input type="file" accept=".jpg,.jpeg,.png,.pdf" onChange={(e) => setDocFile(e.target.files[0])}
                        className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary file:text-white hover:file:bg-blue-700" />
                    </div>
                    <button type="submit" disabled={uploading || !docFile}
                      className="w-full bg-green-600 text-white py-2 rounded-lg font-medium text-sm hover:bg-green-700 disabled:opacity-50">
                      {uploading ? "Uploading..." : "Upload Document ✓"}
                    </button>
                  </form>
                ) : (
                  <div>
                    <p className="text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg mb-3">✓ Document uploaded! Run extraction below.</p>
                    <DocumentExtractor documentId={createdDocId} />
                    <button onClick={() => { resetForm(); fetchApplications(); }}
                      className="w-full mt-4 border border-gray-200 text-gray-600 py-2 rounded-lg text-sm hover:bg-gray-50">
                      Done — Back to Applications
                    </button>
                  </div>
                )}
                {error && <p className="mt-3 text-red-500 text-sm bg-red-50 px-3 py-2 rounded-lg">{error}</p>}
              </div>
            )}

            <div className="space-y-3">
              {applications.length === 0 ? (
                <div className="text-center py-12 text-gray-400">
                  <p className="text-lg">No applications yet</p>
                  <p className="text-sm mt-1">Click "+ New Application" to get started</p>
                </div>
              ) : (
                applications.map((app) => (
                  <div key={app.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex justify-between items-center">
                    <div>
                      <p className="font-medium text-gray-800 capitalize">{app.cert_type.replace(/_/g, " ")}</p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        ID: {app.id.slice(0, 8)}... · {new Date(app.submitted_at).toLocaleDateString("en-IN")}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      {app.predicted_days && <span className="text-xs text-gray-500">~{Math.round(app.predicted_days)} days</span>}
                      <span className={`text-xs px-2 py-1 rounded-full font-medium capitalize ${STATUS_COLORS[app.status] || "bg-gray-100 text-gray-600"}`}>
                        {app.status.replace(/_/g, " ")}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {activeTab === "complaints" && <ComplaintForm />}
        {activeTab === "assistant" && <ChatWidget />}
      </div>
    </div>
  );
}
