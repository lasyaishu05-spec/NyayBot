// src/components/LanguageSelector.jsx

import { LANGUAGES } from "../data/mockData";

export default function LanguageSelector({ lang, setLang }) {
  return (
    <div
      style={{
        background: "#fff",
        borderRadius: 16,
        padding: 24,
        border: "1px solid #E2E8F0",
        boxShadow: "0 2px 12px rgba(0,0,0,0.04)",
        marginBottom: 28,
      }}
    >
      <p
        style={{
          fontFamily: "'Playfair Display', Georgia, serif",
          fontWeight: 700,
          fontSize: 16,
          color: "#0F172A",
          marginBottom: 16,
        }}
      >
        Choose Output Language
      </p>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))",
          gap: 10,
        }}
      >
        {LANGUAGES.map((language) => (
          <button
            key={language.code}
            onClick={() => setLang(language.code)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "10px 14px",
              borderRadius: 12,
              cursor: "pointer",
              border: `2px solid ${lang === language.code ? "#2563EB" : "#E2E8F0"}`,
              background: lang === language.code ? "#EFF6FF" : "#FAFAFA",
              transition: "all 0.15s",
              fontFamily: "Georgia, serif",
            }}
          >
            <span style={{ fontSize: 14, fontWeight: 700, minWidth: 24 }}>{language.flag}</span>
            <div style={{ textAlign: "left" }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: lang === language.code ? "#2563EB" : "#374151",
                }}
              >
                {language.label}
              </div>
              <div style={{ fontSize: 11, color: "#94A3B8" }}>{language.native}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
