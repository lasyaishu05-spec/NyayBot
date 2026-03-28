// src/components/ProcessingLoader.jsx

import { useState, useEffect, useRef } from "react";
import { PROCESSING_STEPS, LANGUAGES } from "../data/mockData";

const STEP_DURATION_MS = 1000;
const PROGRESS_TICK_MS = 100;
const PROGRESS_INCREMENT = 2;

export default function ProcessingLoader({ file, lang, onDone }) {
  const [step, setStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [isWakingUp, setIsWakingUp] = useState(false);
  const calledRef = useRef(false);

  const selectedLang = LANGUAGES.find((language) => language.code === lang);
  const languageName = selectedLang?.label || "English";

  useEffect(() => {
    // Wake-up message timer (for Render cold starts)
    const wakeUpTimer = setTimeout(() => {
      setIsWakingUp(true);
    }, 5000);

    if (calledRef.current) return;
    calledRef.current = true;

    const processDocument = async () => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("language", languageName);

      const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const isLocalHost = API_BASE_URL.includes("localhost") || API_BASE_URL.includes("127.0.0.1");
      const isProduction = window.location.hostname.includes("vercel.app");

      try {
        // Validation: If live on Vercel but trying to reach Localhost
        if (isProduction && isLocalHost) {
          throw new Error("API_URL_NOT_CONFIGURED");
        }

        const res = await fetch(`${API_BASE_URL}/process`, {
          method: "POST",
          body: formData,
        });

        if (!res.ok) {
          throw new Error(`Server responded with status ${res.status}`);
        }

        const data = await res.json();
        clearTimeout(wakeUpTimer);
        setProgress(100);
        onDone(data);
      } catch (error) {
        clearTimeout(wakeUpTimer);
        console.error("Error processing document:", error);
        setProgress(100);

        if (error.message === "API_URL_NOT_CONFIGURED") {
          onDone({
            summary: "⚠️ Missing API Configuration",
            content: `Your website is live, but it doesn't know where your AI backend is located.\n\n### How to Fix:\n1. Go to your **Vercel Settings** -> **Environment Variables**.\n2. Add a new variable called **VITE_API_URL**.\n3. Paste your **Render.com** link (e.g. https://...onrender.com) as the value.\n4. **Redeploy** the project.`,
            actions: ["Add VITE_API_URL to Vercel", "Redeploy the project"],
          });
        } else {
          onDone({
            summary: "Could not connect to the AI analysis server.",
            content: `Error Details: ${error.message}\n\nPlease ensure the backend service is active and accessible at ${API_BASE_URL}.`,
            actions: [
              "Check if your Render.com backend is 'Live'",
              "Verify your internet connection",
              "Ensure VITE_API_URL is correct in Vercel settings",
            ],
          });
        }
      }
    };

    processDocument();

    const stepTimer = setInterval(() => {
      setStep((currentStep) => {
        const next = Math.min(currentStep + 1, PROCESSING_STEPS.length - 1);
        if (next >= PROCESSING_STEPS.length - 1) {
          clearInterval(stepTimer);
        }
        return next;
      });
    }, STEP_DURATION_MS);

    const progressTimer = setInterval(() => {
      setProgress((currentProgress) => Math.min(currentProgress + PROGRESS_INCREMENT, 95));
    }, PROGRESS_TICK_MS);

    return () => {
      clearInterval(stepTimer);
      clearInterval(progressTimer);
    };
  }, [file, languageName, onDone]);

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
      <div
        style={{
          width: "100%",
          maxWidth: 520,
          textAlign: "center",
          animation: "fadeSlideUp 0.5s ease",
        }}
      >
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: "50%",
            border: "4px solid #E0EAFF",
            borderTop: "4px solid #2563EB",
            margin: "0 auto 32px",
            animation: "spin 1s linear infinite",
          }}
        />

        <h2
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: 26,
            fontWeight: 800,
            color: "#0F172A",
            marginBottom: 8,
          }}
        >
          Analyzing Your Document
        </h2>
        <p
          style={{
            color: "#64748B",
            fontFamily: "Georgia, serif",
            fontSize: 15,
            marginBottom: 40,
          }}
        >
          Our AI is working through the legal language...
        </p>

        {isWakingUp && (
          <div style={{
            background: "#FFF7ED",
            border: "1px solid #FFEDD5",
            borderRadius: 12,
            padding: "10px 16px",
            marginBottom: 24,
            display: "flex",
            alignItems: "center",
            gap: 10,
            animation: "pulse 2s infinite",
          }}>
            <span style={{ fontSize: 18 }}>☕</span>
            <span style={{
              color: "#9A3412",
              fontSize: 13,
              fontWeight: 600,
              fontFamily: "Georgia, serif",
              textAlign: "left"
            }}>
              AI service is starting up (this takes ~30s on free plans)...
            </span>
          </div>
        )}

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 12,
            marginBottom: 40,
            textAlign: "left",
          }}
        >
          {PROCESSING_STEPS.map((processingStep, index) => (
            <div
              key={processingStep}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 14,
                padding: "12px 18px",
                borderRadius: 12,
                background:
                  index < step ? "#F0FDF4" : index === step ? "#EFF6FF" : "#F8FAFC",
                border: `1px solid ${
                  index < step ? "#BBF7D0" : index === step ? "#BFDBFE" : "#F1F5F9"
                }`,
                transition: "all 0.4s",
              }}
            >
              <div
                style={{
                  width: 24,
                  height: 24,
                  borderRadius: "50%",
                  flexShrink: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background:
                    index < step ? "#22C55E" : index === step ? "#2563EB" : "#E2E8F0",
                  fontSize: 10,
                  color: "#fff",
                  fontWeight: 700,
                }}
              >
                {index < step ? (
                  "OK"
                ) : index === step ? (
                  <span
                    style={{
                      width: 10,
                      height: 10,
                      borderRadius: "50%",
                      background: "#fff",
                      display: "block",
                      animation: "pulse 1s infinite",
                    }}
                  />
                ) : null}
              </div>
              <span
                style={{
                  fontFamily: "Georgia, serif",
                  fontSize: 14,
                  color: index < step ? "#166534" : index === step ? "#1D4ED8" : "#94A3B8",
                  fontWeight: index === step ? 600 : 400,
                }}
              >
                {processingStep}
              </span>
            </div>
          ))}
        </div>

        <div
          style={{
            background: "#E2E8F0",
            borderRadius: 100,
            height: 8,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              height: "100%",
              borderRadius: 100,
              background: "linear-gradient(90deg, #2563EB, #60A5FA)",
              width: `${progress}%`,
              transition: "width 0.1s linear",
            }}
          />
        </div>
        <p
          style={{
            color: "#94A3B8",
            fontSize: 13,
            marginTop: 8,
            fontFamily: "Georgia, serif",
          }}
        >
          {progress}% complete
        </p>
      </div>
    </div>
  );
}
