// src/components/AnalysisHistory.jsx
import { useState, useEffect } from "react";
import { db } from "../firebase";
import { collection, query, orderBy, getDocs } from "firebase/firestore";
import { useAuth } from "../context/AuthContext";

export default function AnalysisHistory({ onSelect, onBack }) {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const fetchHistory = async () => {
      try {
        const q = query(
          collection(db, "users", user.uid, "analyses"),
          orderBy("timestamp", "desc")
        );
        const querySnapshot = await getDocs(q);
        const docs = querySnapshot.docs.map(doc => ({
          id: doc.id,
          ...doc.data()
        }));
        setAnalyses(docs);
      } catch (err) {
        console.error("Error fetching history:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [user]);

  return (
    <div style={{
      minHeight: "calc(100vh - 60px)",
      background: "#F8FAFC",
      padding: "40px 24px",
    }}>
      <div style={{ maxWidth: "800px", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
          <div>
            <h2 style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: "32px", fontWeight: 800, color: "#0F172A",
            }}>Your Analysis History</h2>
            <p style={{ color: "#64748B", marginTop: "4px" }}>Revisit your previously simplified legal documents.</p>
          </div>
          <button onClick={onBack} style={{
            padding: "10px 20px", borderRadius: "10px", background: "#fff",
            border: "1px solid #E2E8F0", color: "#64748B", fontWeight: 600, cursor: "pointer",
          }}>Back to Home</button>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "60px" }}>
            <div style={{
              width: "40px", height: "40px", border: "4px solid #E2E8F0",
              borderTop: "4px solid #2563EB", borderRadius: "50%",
              margin: "0 auto 16px", animation: "spin 1s linear infinite",
            }} />
            <p style={{ color: "#64748B" }}>Loading history...</p>
          </div>
        ) : analyses.length === 0 ? (
          <div style={{
            background: "#fff", borderRadius: "20px", padding: "60px 40px",
            textAlign: "center", border: "1px dashed #E2E8F0",
          }}>
            <span style={{ fontSize: "48px", display: "block", marginBottom: "16px" }}>📂</span>
            <h3 style={{ fontSize: "20px", fontWeight: 700, color: "#334155" }}>No history found</h3>
            <p style={{ color: "#64748B", marginTop: "8px", maxWidth: "320px", margin: "8px auto" }}>
              Analyses you perform while signed in will appear here.
            </p>
            <button onClick={onBack} style={{
              marginTop: "24px", padding: "12px 28px", borderRadius: "12px",
              background: "#2563EB", color: "#fff", fontWeight: 700, border: "none", cursor: "pointer",
            }}>Start New Analysis</button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {analyses.map((item) => (
              <div
                key={item.id}
                onClick={() => onSelect(item)}
                style={{
                  background: "#fff", padding: "24px", borderRadius: "16px",
                  border: "1px solid #E2E8F0", cursor: "pointer", transition: "all 0.2s",
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = "translateY(-2px)";
                  e.currentTarget.style.boxShadow = "0 10px 25px rgba(0,0,0,0.05)";
                  e.currentTarget.style.borderColor = "#BFDBFE";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "translateY(0)";
                  e.currentTarget.style.boxShadow = "none";
                  e.currentTarget.style.borderColor = "#E2E8F0";
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "6px" }}>
                    <span style={{
                      background: "#EFF6FF", color: "#2563EB", padding: "4px 10px",
                      borderRadius: "8px", fontSize: "12px", fontWeight: 700,
                    }}>
                      {item.docType?.type || "Legal Document"}
                    </span>
                    <span style={{ fontSize: "13px", color: "#94A3B8" }}>
                      {item.timestamp?.toDate().toLocaleDateString('en-IN', {
                        day: 'numeric', month: 'short', year: 'numeric'
                      })}
                    </span>
                  </div>
                  <h4 style={{ fontSize: "18px", fontWeight: 700, color: "#1E293B" }}>{item.fileName}</h4>
                  <p style={{
                    fontSize: "14px", color: "#64748B", marginTop: "4px",
                    display: "-webkit-box", WebkitLineClamp: "1", WebkitBoxOrient: "vertical",
                    overflow: "hidden", maxWidth: "500px",
                  }}>
                    {item.shortSummary?.replace(/•/g, '').split('\n')[0]}
                  </p>
                </div>
                <div style={{
                  width: "40px", height: "40px", borderRadius: "50%",
                  background: "#F8FAFC", display: "flex", alignItems: "center",
                  justifyContent: "center", color: "#2563EB", fontSize: "18px",
                }}>
                  →
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <style>{`
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}
