import { useState } from "react";
import HowItWorksModal from "./HowItWorksModal";

export default function Navbar({ onReset }) {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <header
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          background: "rgba(255,255,255,0.92)",
          backdropFilter: "blur(12px)",
          borderBottom: "1px solid #E8EEFA",
          boxShadow: "0 1px 0 0 #E8EEFA",
        }}
      >
        <div
          style={{
            maxWidth: 1200,
            margin: "0 auto",
            padding: "0 24px",
            height: 60,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <button
            onClick={onReset}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              background: "none",
              border: "none",
              cursor: "pointer",
              padding: 0,
            }}
          >
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: 10,
                background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 2px 8px rgba(37,99,235,0.3)",
              }}
            >
              <span style={{ color: "#fff", fontSize: 14, fontWeight: 700 }}>NB</span>
            </div>
            <span
              style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontWeight: 700,
                fontSize: 20,
                color: "#0F172A",
                letterSpacing: "-0.3px",
              }}
            >
              NyayBot
            </span>
          </button>

          <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
            <span
              style={{
                fontSize: 13,
                color: "#64748B",
                fontFamily: "Georgia, serif",
                fontStyle: "italic",
              }}
            >
              Legal clarity for every citizen
            </span>
            <button
              onClick={() => setIsModalOpen(true)}
              style={{
                fontSize: 13,
                fontWeight: 500,
                color: "#2563EB",
                background: "none",
                border: "none",
                textDecoration: "none",
                fontFamily: "Georgia, serif",
                cursor: "pointer",
                padding: 0,
              }}
            >
              How it works
            </button>
          </div>
        </div>
      </header>

      <HowItWorksModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}
