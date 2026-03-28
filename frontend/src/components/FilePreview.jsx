// src/components/FilePreview.jsx

import { useState, useEffect } from "react";
import LanguageSelector from "./LanguageSelector";

export default function FilePreview({ file, lang, setLang, onProcess, onRemove }) {
  const [preview, setPreview] = useState(null);

  const isImage = file?.type?.startsWith("image/");

  useEffect(() => {
    if (!isImage) return;

    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target.result);
    reader.readAsDataURL(file);
  }, [file, isImage]);

  const sizeLabel = `${(file.size / 1024).toFixed(1)} KB`;

  return (
    <div
      style={{
        minHeight: "calc(100vh - 60px)",
        background: "linear-gradient(160deg, #EFF6FF 0%, #F8FAFC 60%, #F0FDF4 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 24px",
      }}
    >
      <div style={{ width: "100%", maxWidth: 620, animation: "fadeSlideUp 0.5s ease" }}>
        <h2
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: 28,
            fontWeight: 800,
            color: "#0F172A",
            textAlign: "center",
            marginBottom: 8,
          }}
        >
          Configure & Process
        </h2>
        <p
          style={{
            textAlign: "center",
            color: "#64748B",
            marginBottom: 32,
            fontFamily: "Georgia, serif",
            fontSize: 15,
          }}
        >
          Select your preferred language and start analysis
        </p>

        <div
          style={{
            background: "#fff",
            borderRadius: 16,
            padding: 20,
            border: "1px solid #E2E8F0",
            boxShadow: "0 2px 12px rgba(0,0,0,0.04)",
            display: "flex",
            alignItems: "center",
            gap: 16,
            marginBottom: 24,
          }}
        >
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 12,
              background: "#EFF6FF",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 14,
              fontWeight: 700,
              flexShrink: 0,
              color: "#2563EB",
            }}
          >
            {file.type === "application/pdf" ? "PDF" : "IMG"}
          </div>

          {isImage && preview && (
            <img
              src={preview}
              alt="preview"
              style={{ width: 52, height: 52, objectFit: "cover", borderRadius: 10 }}
            />
          )}

          <div style={{ flex: 1 }}>
            <p
              style={{
                fontWeight: 700,
                color: "#0F172A",
                fontFamily: "Georgia, serif",
                fontSize: 15,
                marginBottom: 2,
              }}
            >
              {file.name}
            </p>
            <p style={{ color: "#94A3B8", fontSize: 13, fontFamily: "Georgia, serif" }}>
              {sizeLabel}
            </p>
          </div>

          <button
            onClick={onRemove}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              color: "#94A3B8",
              fontSize: 18,
              padding: 8,
              borderRadius: 8,
              transition: "color 0.2s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "#EF4444";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "#94A3B8";
            }}
          >
            x
          </button>
        </div>

        <LanguageSelector lang={lang} setLang={setLang} />

        <button
          onClick={onProcess}
          style={{
            width: "100%",
            padding: "16px",
            borderRadius: 14,
            background: "linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%)",
            color: "#fff",
            fontWeight: 700,
            fontSize: 16,
            border: "none",
            cursor: "pointer",
            boxShadow: "0 4px 20px rgba(37,99,235,0.3)",
            fontFamily: "Georgia, serif",
            transition: "transform 0.2s, box-shadow 0.2s",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = "translateY(-1px)";
            e.currentTarget.style.boxShadow = "0 8px 28px rgba(37,99,235,0.4)";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = "0 4px 20px rgba(37,99,235,0.3)";
          }}
        >
          Analyze & Simplify Document
        </button>
      </div>
    </div>
  );
}
