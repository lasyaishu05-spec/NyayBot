// src/components/AuthModal.jsx
import { useState, useEffect, useRef } from "react";
import { RecaptchaVerifier, signInWithPhoneNumber, GoogleAuthProvider, signInWithPopup } from "firebase/auth";
import { auth } from "../firebase";

export default function AuthModal({ isOpen, onClose }) {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [verificationId, setVerificationId] = useState("");
  const [otp, setOtp] = useState("");
  const [step, setStep] = useState(1); // 1: Phone, 2: OTP
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const recaptchaRef = useRef(null);

  const onGoogleSignIn = async () => {
    setLoading(true);
    setError("");
    try {
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      onClose();
    } catch (err) {
      console.error(err);
      setError("Failed to sign in with Google. Check your network or Firebase console.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && !window.recaptchaVerifier) {
      window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
        size: 'invisible',
        callback: (response) => {
          // reCAPTCHA solved, allow signInWithPhoneNumber.
        }
      });
    }
  }, [isOpen]);

  const onSendOTP = async () => {
    if (!phoneNumber) return setError("Please enter a phone number.");
    setLoading(true);
    setError("");
    try {
      const appVerifier = window.recaptchaVerifier;
      const formatPhone = phoneNumber.startsWith("+") ? phoneNumber : `+91${phoneNumber}`;
      const confirmationResult = await signInWithPhoneNumber(auth, formatPhone, appVerifier);
      window.confirmationResult = confirmationResult;
      setStep(2);
    } catch (err) {
      console.error(err);
      setError("Failed to send OTP. Check your number or reCAPTCHA.");
      if (window.recaptchaVerifier) window.recaptchaVerifier.clear();
      window.recaptchaVerifier = null;
    } finally {
      setLoading(false);
    }
  };

  const onVerifyOTP = async () => {
    if (!otp) return setError("Please enter the OTP.");
    setLoading(true);
    setError("");
    try {
      await window.confirmationResult.confirm(otp);
      onClose();
    } catch (err) {
      console.error(err);
      setError("Invalid OTP. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
      background: "rgba(15, 23, 42, 0.4)", backdropFilter: "blur(8px)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000,
    }}>
      <div style={{
        background: "#fff", padding: "40px", borderRadius: "24px", maxWidth: "420px",
        width: "90%", boxShadow: "0 20px 40px rgba(0,0,0,0.1)", textAlign: "center",
      }}>
        <h2 style={{
          fontFamily: "'Playfair Display', Georgia, serif", fontSize: "28px",
          fontWeight: 800, color: "#0F172A", marginBottom: "12px",
        }}>NyayBot Login</h2>
        <p style={{ color: "#64748B", marginBottom: "32px", fontSize: "15px" }}>
          Sign in to save your document history
        </p>

        {error && <div style={{
          background: "#FEE2E2", color: "#DC2626", padding: "12px",
          borderRadius: "12px", fontSize: "14px", marginBottom: "20px",
        }}>{error}</div>}

        <div id="recaptcha-container"></div>

        {/* Primary Action: Google */}
        {step === 1 && (
          <>
            <button
              onClick={onGoogleSignIn}
              disabled={loading}
              style={{
                width: "100%", padding: "14px", borderRadius: "12px",
                background: "#fff", color: "#1F2937", fontWeight: 700,
                border: "1px solid #E2E8F0", cursor: loading ? "not-allowed" : "pointer",
                display: "flex", alignItems: "center", justifyContent: "center", gap: "12px",
                boxShadow: "0 2px 8px rgba(0,0,0,0.05)", marginBottom: "24px",
                transition: "all 0.2s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "#F9FAFB";
                e.currentTarget.style.borderColor = "#CBD5E1";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "#fff";
                e.currentTarget.style.borderColor = "#E2E8F0";
              }}
            >
              <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width="18" height="18" alt="G" />
              Continue with Google
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "24px" }}>
              <div style={{ flex: 1, height: "1px", background: "#E2E8F0" }}></div>
              <span style={{ fontSize: "12px", color: "#94A3B8", fontWeight: 600 }}>OR</span>
              <div style={{ flex: 1, height: "1px", background: "#E2E8F0" }}></div>
            </div>
          </>
        )}

        {step === 1 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <input
              type="tel"
              placeholder="+91 9876543210"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              style={{
                width: "100%", padding: "14px 18px", borderRadius: "12px",
                border: "1px solid #E2E8F0", fontSize: "16px", outline: "none",
              }}
            />
            <button
              onClick={onSendOTP}
              disabled={loading}
              style={{
                width: "100%", padding: "14px", borderRadius: "12px",
                background: "#2563EB", color: "#fff", fontWeight: 700,
                border: "none", cursor: loading ? "not-allowed" : "pointer",
                boxShadow: "0 4px 12px rgba(37,99,235,0.2)",
              }}
            >
              {loading ? "Sending..." : "Sign in with Phone"}
            </button>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <p style={{ color: "#64748B", marginBottom: "16px", fontSize: "14px" }}>
              Enter the 6-digit code sent to {phoneNumber}
            </p>
            <input
              type="text"
              maxLength="6"
              placeholder="000000"
              value={otp}
              onChange={(e) => setOtp(e.target.value)}
              style={{
                width: "100%", padding: "14px 18px", borderRadius: "12px",
                border: "1px solid #E2E8F0", fontSize: "16px", textAlign: "center",
                letterSpacing: "8px", fontWeight: "700", outline: "none",
              }}
            />
            <button
              onClick={onVerifyOTP}
              disabled={loading}
              style={{
                width: "100%", padding: "14px", borderRadius: "12px",
                background: "#22C55E", color: "#fff", fontWeight: 700,
                border: "none", cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Verifying..." : "Verify OTP"}
            </button>
            <button
              onClick={() => setStep(1)}
              style={{
                background: "none", border: "none", color: "#64748B",
                fontSize: "14px", cursor: "pointer", textDecoration: "underline",
              }}
            >
              Back to change number
            </button>
          </div>
        )}

        <button
          onClick={onClose}
          style={{
            marginTop: "24px", background: "none", border: "none",
            color: "#94A3B8", fontSize: "14px", cursor: "pointer",
          }}
        >
          Close
        </button>
      </div>
    </div>
  );
}
