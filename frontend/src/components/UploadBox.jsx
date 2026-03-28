// src/components/UploadBox.jsx

import { useState, useRef, useCallback } from "react";

const ACCEPTED_TYPES = ["application/pdf", "image/jpeg", "image/png"];
const MAX_SIZE_MB = 20;

export default function UploadBox({ onFileSelected }) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef();

  const handleFile = useCallback(
    (file) => {
      if (!file) return;

      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError("Unsupported file type. Please upload a PDF, JPG, or PNG.");
        return;
      }
      if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        setError(`File too large. Maximum size is ${MAX_SIZE_MB}MB.`);
        return;
      }

      setError("");
      onFileSelected(file);
    },
    [onFileSelected]
  );

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setDragging(false);
      handleFile(e.dataTransfer.files[0]);
    },
    [handleFile]
  );

  return (
    <div
      style={{
        minHeight: "calc(100vh - 60px)",
        background: "linear-gradient(160deg, #EFF6FF 0%, #F8FAFC 60%, #FFF7ED 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "40px 24px",
      }}
    >
      <div style={{ width: "100%", maxWidth: 580, animation: "fadeSlideUp 0.5s ease" }}>
        <h2
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: 32,
            fontWeight: 800,
            color: "#0F172A",
            textAlign: "center",
            marginBottom: 8,
            letterSpacing: "-0.5px",
          }}
        >
          Upload Your Document
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
          Supports PDF, JPG, PNG up to {MAX_SIZE_MB}MB
        </p>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current.click()}
          style={{
            border: `2px dashed ${dragging ? "#2563EB" : "#CBD5E1"}`,
            borderRadius: 20,
            background: dragging ? "#EFF6FF" : "#FAFCFF",
            padding: "56px 32px",
            textAlign: "center",
            cursor: "pointer",
            transition: "all 0.2s",
            boxShadow: dragging ? "0 0 0 4px rgba(37,99,235,0.1)" : "none",
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            style={{ display: "none" }}
            onChange={(e) => handleFile(e.target.files[0])}
          />
          <div style={{ fontSize: 32, fontWeight: 700, marginBottom: 16 }}>DOC</div>
          <p
            style={{
              fontFamily: "Georgia, serif",
              fontWeight: 700,
              fontSize: 18,
              color: "#0F172A",
              marginBottom: 8,
            }}
          >
            Drag & drop your file here
          </p>
          <p style={{ color: "#94A3B8", fontSize: 14, fontFamily: "Georgia, serif" }}>
            or click to browse
          </p>
          <div style={{ display: "flex", gap: 10, justifyContent: "center", marginTop: 20 }}>
            {["PDF", "JPG", "PNG"].map((format) => (
              <span
                key={format}
                style={{
                  background: "#EFF6FF",
                  color: "#2563EB",
                  fontSize: 11,
                  fontWeight: 700,
                  padding: "4px 10px",
                  borderRadius: 6,
                  letterSpacing: "0.5px",
                }}
              >
                {format}
              </span>
            ))}
          </div>
        </div>

        {error && (
          <div
            style={{
              marginTop: 16,
              background: "#FEF2F2",
              border: "1px solid #FECACA",
              borderRadius: 12,
              padding: "12px 16px",
              display: "flex",
              gap: 10,
              alignItems: "center",
            }}
          >
            <span>!</span>
            <span style={{ color: "#DC2626", fontSize: 14, fontFamily: "Georgia, serif" }}>
              {error}
            </span>
          </div>
        )}

        <p
          style={{
            textAlign: "center",
            color: "#94A3B8",
            fontSize: 13,
            marginTop: 24,
            fontFamily: "Georgia, serif",
          }}
        >
          Your document is processed securely and never stored.
        </p>
      </div>
    </div>
  );
}
