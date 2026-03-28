// src/components/HowItWorksModal.jsx

export default function HowItWorksModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(15, 23, 42, 0.6)",
        backdropFilter: "blur(4px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
        animation: "fadeSlideUp 0.3s ease",
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: "20px",
          width: "100%",
          maxWidth: "600px",
          padding: "32px",
          position: "relative",
          boxShadow: "0 20px 40px rgba(0,0,0,0.15)",
        }}
      >
        <button
          onClick={onClose}
          style={{
            position: "absolute",
            top: "20px",
            right: "20px",
            background: "#F1F5F9",
            border: "none",
            width: "36px",
            height: "36px",
            borderRadius: "50%",
            fontSize: "18px",
            color: "#64748B",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#E2E8F0";
            e.currentTarget.style.color = "#0F172A";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "#F1F5F9";
            e.currentTarget.style.color = "#64748B";
          }}
        >
          x
        </button>

        <h2
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: "28px",
            fontWeight: "800",
            color: "#0F172A",
            marginBottom: "8px",
          }}
        >
          How NyayBot Works
        </h2>
        <p
          style={{
            color: "#64748B",
            fontFamily: "Georgia, serif",
            fontSize: "15px",
            marginBottom: "32px",
          }}
        >
          We make confusing legal documents easy for everyone to understand.
        </p>

        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          <Step
            number="1"
            label="DOC"
            title="Upload Your Document"
            text="Take any legal document like a rental agreement, court notice, or contract and securely upload it as a PDF or image."
          />
          <Step
            number="2"
            label="AI"
            title="AI Explains It Simply"
            text="Our AI reads dense legal jargon and pulls out the most important terms, dates, money, and obligations into simple bullet points."
          />
          <Step
            number="3"
            label="IN"
            title="Translated For You"
            text="Select from 12 Indian languages including Hindi, Tamil, and Telugu. The simplified explanation is translated immediately."
          />
          <Step
            number="4"
            label="OK"
            title="Clear Action Steps"
            text="We provide a handy checklist of what you need to do next, like signing a page or paying a deposit by a specific date."
          />
        </div>

        <button
          onClick={onClose}
          style={{
            width: "100%",
            marginTop: "32px",
            padding: "14px",
            background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
            color: "#fff",
            fontWeight: "700",
            fontSize: "15px",
            borderRadius: "12px",
            border: "none",
            cursor: "pointer",
            fontFamily: "Georgia, serif",
            boxShadow: "0 4px 12px rgba(37,99,235,0.25)",
            transition: "transform 0.2s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-2px)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
          }}
        >
          Got it, let's start!
        </button>
      </div>
    </div>
  );
}

function Step({ number, label, title, text }) {
  return (
    <div style={{ display: "flex", gap: "16px", alignItems: "flex-start" }}>
      <div
        style={{
          flexShrink: 0,
          width: "40px",
          height: "40px",
          background: "#EFF6FF",
          borderRadius: "12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          border: "1px solid #BFDBFE",
          fontSize: "14px",
          fontWeight: 700,
          color: "#2563EB",
        }}
      >
        {label}
      </div>
      <div>
        <h4
          style={{
            color: "#0F172A",
            fontSize: "16px",
            fontWeight: "700",
            marginBottom: "4px",
            fontFamily: "Georgia, serif",
          }}
        >
          Step {number}: {title}
        </h4>
        <p
          style={{
            color: "#475569",
            fontSize: "14px",
            lineHeight: "1.6",
            fontFamily: "Georgia, serif",
          }}
        >
          {text}
        </p>
      </div>
    </div>
  );
}
