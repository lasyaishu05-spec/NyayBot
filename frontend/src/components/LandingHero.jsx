// src/components/LandingHero.jsx

const TRUST_BADGES = [
  { icon: "Secure", label: "Bank-grade Encryption" },
  { icon: "Fast", label: "Results in under 30s" },
  { icon: "India", label: "Indian Law Trained" },
];

const DOC_TYPES = [
  { icon: "RA", label: "Rent Agreements" },
  { icon: "CN", label: "Court Notices" },
  { icon: "PD", label: "Property Deeds" },
  { icon: "EC", label: "Employment Contracts" },
  { icon: "LD", label: "Loan Documents" },
];

export default function LandingHero({ onGetStarted }) {
  return (
    <div
      style={{
        minHeight: "calc(100vh - 60px)",
        background: "linear-gradient(160deg, #EFF6FF 0%, #F8FAFC 50%, #F0FDF4 100%)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "60px 24px",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -80,
          right: -80,
          width: 400,
          height: 400,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(37,99,235,0.06) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: -120,
          left: -60,
          width: 500,
          height: 500,
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(16,185,129,0.05) 0%, transparent 70%)",
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 8,
          background: "#EFF6FF",
          border: "1px solid #BFDBFE",
          borderRadius: 100,
          padding: "6px 16px",
          marginBottom: 28,
          animation: "fadeSlideUp 0.5s ease",
        }}
      >
        <span style={{ fontSize: 12, fontWeight: 700 }}>IN</span>
        <span
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: "#2563EB",
            letterSpacing: "0.5px",
            fontFamily: "Georgia, serif",
          }}
        >
          12 INDIAN LANGUAGES SUPPORTED
        </span>
      </div>

      <h1
        style={{
          fontFamily: "'Playfair Display', Georgia, serif",
          fontSize: "clamp(36px, 5vw, 64px)",
          fontWeight: 800,
          color: "#0F172A",
          textAlign: "center",
          maxWidth: 720,
          lineHeight: 1.15,
          letterSpacing: "-1px",
          marginBottom: 20,
          animation: "fadeSlideUp 0.6s ease",
        }}
      >
        Understand Legal Documents <span style={{ color: "#2563EB" }}>in Minutes</span>
      </h1>

      <p
        style={{
          fontSize: 18,
          color: "#475569",
          textAlign: "center",
          maxWidth: 520,
          lineHeight: 1.7,
          fontFamily: "Georgia, serif",
          marginBottom: 40,
          animation: "fadeSlideUp 0.7s ease",
        }}
      >
        Upload. Simplify. Translate. Act.{" "}
        <span style={{ color: "#64748B" }}>
          NyayBot decodes complex legal jargon into plain language in your mother tongue.
        </span>
      </p>

      <button
        onClick={onGetStarted}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 10,
          background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
          color: "#fff",
          fontWeight: 700,
          fontSize: 16,
          padding: "16px 36px",
          borderRadius: 14,
          border: "none",
          cursor: "pointer",
          boxShadow: "0 4px 24px rgba(37,99,235,0.35)",
          transition: "transform 0.2s, box-shadow 0.2s",
          fontFamily: "Georgia, serif",
          animation: "fadeSlideUp 0.8s ease",
          position: "relative",
          zIndex: 10,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "translateY(-2px)";
          e.currentTarget.style.boxShadow = "0 8px 32px rgba(37,99,235,0.45)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow = "0 4px 24px rgba(37,99,235,0.35)";
        }}
      >
        <span>DOC</span> Upload Document
      </button>

      <div
        style={{
          display: "flex",
          gap: 32,
          marginTop: 56,
          flexWrap: "wrap",
          justifyContent: "center",
          animation: "fadeSlideUp 0.9s ease",
        }}
      >
        {TRUST_BADGES.map((badge) => (
          <div
            key={badge.label}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              color: "#64748B",
              fontSize: 13,
              fontFamily: "Georgia, serif",
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 700 }}>{badge.icon}</span>
            {badge.label}
          </div>
        ))}
      </div>

      <div
        style={{
          marginTop: 64,
          display: "flex",
          gap: 16,
          flexWrap: "wrap",
          justifyContent: "center",
          animation: "fadeSlideUp 1s ease",
        }}
      >
        {DOC_TYPES.map((type) => (
          <div
            key={type.label}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: "#fff",
              border: "1px solid #E2E8F0",
              borderRadius: 10,
              padding: "10px 18px",
              fontSize: 13,
              fontWeight: 500,
              color: "#374151",
              boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
              fontFamily: "Georgia, serif",
            }}
          >
            <span style={{ fontSize: 12, fontWeight: 700 }}>{type.icon}</span>
            {type.label}
          </div>
        ))}
      </div>
    </div>
  );
}
