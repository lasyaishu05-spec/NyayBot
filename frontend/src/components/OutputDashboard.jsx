import { useState, useRef, useEffect } from "react";
import { LANGUAGES } from "../data/mockData";

// ─── LANGUAGE CODE MAP ──────────────────────────────────────────────────────
const LANG_CODE_TO_SPEECH = {
  en: "en-IN",  hi: "hi-IN",  te: "te-IN",  ta: "ta-IN",
  kn: "kn-IN",  bn: "bn-IN",  mr: "mr-IN",  gu: "gu-IN",
  ml: "ml-IN",  pa: "pa-IN",  ur: "ur-IN",  or: "or-IN",
};

const langCodeToName = {};
LANGUAGES.forEach((l) => { langCodeToName[l.code] = l.label; });


// ─── MAIN COMPONENT ─────────────────────────────────────────────────────────

export default function OutputDashboard({ file, lang, apiData, onReset }) {
  const [chatMessages, setChatMessages] = useState(() => {
    const saved = localStorage.getItem("nyaybot_chat");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.length > 0) return parsed;
      } catch (e) {}
    }
    return [{ role: "ai", text: "Hi! I've analyzed your document. What would you like to know?" }];
  });

  // Save chat history to local database
  useEffect(() => {
    if (chatMessages.length > 1) {
      localStorage.setItem("nyaybot_chat", JSON.stringify(chatMessages));
    }
  }, [chatMessages]);

  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [summaryMode, setSummaryMode] = useState("short");
  const [isListening, setIsListening] = useState(false);
  const [speakingId, setSpeakingId] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Pre-load voices for Speech Synthesis
  useEffect(() => {
    const loadVoices = () => { window.speechSynthesis.getVoices(); };
    loadVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }
  }, []);

  const selectedLang = LANGUAGES.find((language) => language.code === lang);

  // Auto-scroll chat (only if open AND there is more than the initial message)
  useEffect(() => {
    if (showChat && chatMessages.length > 1) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, showChat]);

  // ─── DATA ───────────────────────────────────────────────────────────────
  const summary = summaryMode === "short"
    ? (apiData?.short_summary || apiData?.summary || "No summary available.")
    : (apiData?.detailed_summary || apiData?.summary || "No summary available.");
  const content = apiData?.content || "No content available.";
  const actions = apiData?.actions || [];
  const docType = apiData?.document_type || { type: "Legal Document", confidence: "medium" };
  const highlights = apiData?.highlights || { dates: [], obligations: [], risks: [] };
  const contentParagraphs = content.split("\n\n").filter((p) => p.trim());
  const summaryBullets = summary.split("\n").filter((l) => l.trim());

  // ─── VOICE INPUT ────────────────────────────────────────────────────────
  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = LANG_CODE_TO_SPEECH[lang] || "en-IN";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setChatInput((prev) => (prev ? prev + " " : "") + transcript);
      setIsListening(false);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setIsListening(true);
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
  };

  const speakingIdRef = useRef(null);
  const audioRef = useRef(null);

  // ─── VOICE OUTPUT (TTS) ────────────────────────────────────────────────
  const speakText = (text, id) => {
    if (speakingIdRef.current === id) {
      window.speechSynthesis.cancel();
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      speakingIdRef.current = null;
      setSpeakingId(null);
      return;
    }
    
    window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    speakingIdRef.current = id;
    setSpeakingId(id);

    const targetLang = LANG_CODE_TO_SPEECH[lang] || "en-IN";
    const baseLang = targetLang.split("-")[0];
    const voices = window.speechSynthesis.getVoices();
    
    let matchedVoice = voices.find((v) => v.lang === targetLang || v.lang.replace('_', '-') === targetLang);
    if (!matchedVoice) {
      matchedVoice = voices.find((v) => v.lang.startsWith(baseLang));
    }
    if (!matchedVoice) {
      matchedVoice = voices.find(v => v.lang.includes(baseLang) || v.name.toLowerCase().includes(baseLang));
    }

    // Split text into chunks, ensuring no chunk exceeds ~200 characters for API safety
    let rawChunks = text.match(/[^.!?\n]+[.!?\n]*/g) || [text];
    const chunks = [];
    rawChunks.forEach(chunk => {
      if (chunk.length <= 190) {
        chunks.push(chunk);
      } else {
        const words = chunk.split(' ');
        let temp = "";
        words.forEach(w => {
          if (temp.length + w.length + 1 > 180) {
            chunks.push(temp);
            temp = w + " ";
          } else {
            temp += w + " ";
          }
        });
        if (temp.trim()) chunks.push(temp);
      }
    });

    let currentChunk = 0;

    // Use Web Speech API if native voice is found locally
    if (matchedVoice) {
      const speakNextChunk = () => {
        if (speakingIdRef.current !== id) return;
        if (currentChunk >= chunks.length) {
          speakingIdRef.current = null;
          setSpeakingId(null);
          return;
        }

        const utterance = new SpeechSynthesisUtterance(chunks[currentChunk]);
        utterance.lang = targetLang;
        utterance.rate = 0.9;
        utterance.voice = matchedVoice;

        utterance.onend = () => {
          currentChunk++;
          speakNextChunk();
        };

        utterance.onerror = (e) => {
          console.error("Speech Synthesis Error:", e);
          currentChunk++; 
          speakNextChunk(); // Keep pushing through errors to prevent lockup
        };

        window.speechSynthesis.speak(utterance);
      };
      speakNextChunk();
    } else {
      // NATIVE VOICE NOT FOUND: Fallback to reliable Google Translate Audio API
      // This solves the issue for Windows machines lacking Indian voice packs!
      const playNextAudioChunk = () => {
        if (speakingIdRef.current !== id) return;
        if (currentChunk >= chunks.length) {
          speakingIdRef.current = null;
          setSpeakingId(null);
          return;
        }

        const textChunk = encodeURIComponent(chunks[currentChunk].trim());
        if (!textChunk) {
          currentChunk++;
          playNextAudioChunk();
          return;
        }

        const url = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${baseLang}&client=tw-ob&q=${textChunk}`;
        const audio = new Audio(url);
        audioRef.current = audio;

        audio.onended = () => {
          currentChunk++;
          playNextAudioChunk();
        };
        
        audio.onerror = () => {
          console.error("Audio API Fallback Error");
          currentChunk++;
          playNextAudioChunk();
        };

        audio.play().catch(e => {
          console.error("Audio play blocked/failed:", e);
          currentChunk++;
          playNextAudioChunk();
        });
      };
      playNextAudioChunk();
    }
  };

  // ─── CHAT ───────────────────────────────────────────────────────────────
  const sendChat = async () => {
    if (!chatInput.trim() || chatLoading) return;
    const userMessage = chatInput.trim();
    setChatInput("");

    setChatMessages((prev) => [
      ...prev,
      { role: "user", text: userMessage },
      { role: "ai", text: "Thinking...", loading: true },
    ]);
    setChatLoading(true);

    const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
    const isLocalHost = API_BASE_URL.includes("localhost") || API_BASE_URL.includes("127.0.0.1");
    const isProduction = window.location.hostname.includes("vercel.app");

    try {
      if (isProduction && isLocalHost) {
        throw new Error("API_URL_NOT_CONFIGURED");
      }

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: userMessage,
          document_content: content,
          language: langCodeToName[lang] || "English",
          history: chatMessages.filter((m) => !m.loading).map((m) => ({ role: m.role, text: m.text })),
        }),
      });
      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const data = await response.json();

      setChatMessages((prev) => {
        const updated = [...prev];
        for (let i = updated.length - 1; i >= 0; i--) {
          if (updated[i].loading) { updated[i] = { role: "ai", text: data.answer }; break; }
        }
        return updated;
      });
    } catch (error) {
      console.error("Chat error:", error);
      setChatMessages((prev) => {
        const updated = [...prev];
        let errorMsg = "Sorry, I couldn't reach the AI assistant right now. Please try again.";
        
        if (error.message === "API_URL_NOT_CONFIGURED") {
          errorMsg = "⚠️ Configuration Missing: Visit your Vercel Settings and add the VITE_API_URL variable (pointing to Render) to enable chat.";
        }

        for (let i = updated.length - 1; i >= 0; i--) {
          if (updated[i].loading) {
            updated[i] = { role: "ai", text: errorMsg };
            break;
          }
        }
        return updated;
      });
    } finally {
      setChatLoading(false);
    }
  };

  // ─── RENDER ─────────────────────────────────────────────────────────────
  return (
    <div style={{ background: "#F8FAFC", minHeight: "calc(100vh - 60px)", paddingBottom: 60 }}>

      {/* ── TOP BAR ── */}
      <div style={{
        background: "#fff", borderBottom: "1px solid #E2E8F0",
        padding: "14px 24px", display: "flex", alignItems: "center",
        justifyContent: "space-between", flexWrap: "wrap", gap: 12,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
          <div style={{
            background: "#DCFCE7", color: "#166534", fontSize: 12,
            fontWeight: 700, padding: "4px 12px", borderRadius: 100, letterSpacing: "0.5px",
          }}>ANALYSIS COMPLETE</div>

          {/* Document Type Badge */}
          <div style={{
            background: "linear-gradient(135deg, #FEF3C7, #FDE68A)",
            color: "#92400E", fontSize: 12, fontWeight: 700,
            padding: "5px 14px", borderRadius: 100,
            border: "1px solid #FCD34D",
            display: "flex", alignItems: "center", gap: 6,
            animation: "fadeSlideUp 0.6s ease",
          }}>
            <span>📄</span>
            <span>{docType.type}</span>
            {docType.confidence === "high" && (
              <span style={{
                background: "#22C55E", color: "#fff", fontSize: 9,
                padding: "1px 6px", borderRadius: 100, fontWeight: 800,
              }}>✓</span>
            )}
          </div>

          <span style={{ fontSize: 14, color: "#64748B", fontFamily: "Georgia, serif" }}>
            {file?.name}
          </span>
          <span style={{
            background: "#EFF6FF", color: "#2563EB", fontSize: 12,
            fontWeight: 600, padding: "4px 10px", borderRadius: 8,
          }}>
            {selectedLang?.flag} {selectedLang?.label}
          </span>
        </div>

        <button onClick={onReset} style={{
          display: "flex", alignItems: "center", gap: 8,
          padding: "8px 16px", borderRadius: 10, background: "#2563EB",
          border: "none", color: "#fff", fontSize: 13, fontWeight: 600,
          cursor: "pointer", fontFamily: "Georgia, serif",
        }}>New Document</button>
      </div>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "24px 24px 0" }}>

        {/* ── SUMMARY CARD ── */}
        <div style={{
          background: "linear-gradient(135deg, #1D4ED8 0%, #2563EB 100%)",
          borderRadius: 20, padding: "24px 28px", marginBottom: 24, color: "#fff",
          boxShadow: "0 4px 24px rgba(37,99,235,0.25)", animation: "fadeSlideUp 0.5s ease",
        }}>
          {/* Summary Toggle + Read Aloud */}
          <div style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            marginBottom: 14, flexWrap: "wrap", gap: 10,
          }}>
            <div style={{ display: "flex", gap: 4, background: "rgba(255,255,255,0.15)", borderRadius: 10, padding: 3 }}>
              <button onClick={() => setSummaryMode("short")} style={{
                padding: "6px 16px", borderRadius: 8, border: "none", cursor: "pointer",
                fontSize: 12, fontWeight: 700, fontFamily: "Georgia, serif",
                background: summaryMode === "short" ? "#fff" : "transparent",
                color: summaryMode === "short" ? "#1D4ED8" : "rgba(255,255,255,0.8)",
                transition: "all 0.2s",
              }}>Short Summary</button>
              <button onClick={() => setSummaryMode("detailed")} style={{
                padding: "6px 16px", borderRadius: 8, border: "none", cursor: "pointer",
                fontSize: 12, fontWeight: 700, fontFamily: "Georgia, serif",
                background: summaryMode === "detailed" ? "#fff" : "transparent",
                color: summaryMode === "detailed" ? "#1D4ED8" : "rgba(255,255,255,0.8)",
                transition: "all 0.2s",
              }}>Detailed Summary</button>
            </div>

            <button onClick={() => speakText(summary, "summary")} style={{
              background: speakingId === "summary" ? "#EF4444" : "rgba(255,255,255,0.2)",
              border: "none", color: "#fff", borderRadius: 10,
              padding: "6px 14px", cursor: "pointer", fontSize: 13, fontWeight: 600,
              display: "flex", alignItems: "center", gap: 6,
              fontFamily: "Georgia, serif", transition: "all 0.2s",
            }}>
              {speakingId === "summary" ? "⏹ Stop" : "🔊 Read Aloud"}
            </button>
          </div>

          <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
            <div style={{ flex: 1 }}>
              <p style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontWeight: 700, fontSize: 18, marginBottom: 10,
              }}>Document Summary</p>
              {summaryMode === "short" ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                  {summaryBullets.map((bullet, i) => (
                    <p key={i} style={{
                      fontSize: 16, lineHeight: 1.7, color: "#BFDBFE",
                      fontFamily: "Georgia, serif",
                      padding: "4px 0",
                    }}>{bullet}</p>
                  ))}
                </div>
              ) : (
                <p style={{
                  fontSize: 17, lineHeight: 1.7, color: "#BFDBFE",
                  fontFamily: "Georgia, serif",
                }}>{summary}</p>
              )}
            </div>
          </div>
        </div>

        {/* ── KEY HIGHLIGHTS ── */}
        {(highlights.dates.length > 0 || highlights.obligations.length > 0 || highlights.risks.length > 0) && (
          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: 16, marginBottom: 24, animation: "fadeSlideUp 0.6s ease",
          }}>
            {/* Dates */}
            {highlights.dates.length > 0 && (
              <HighlightCard
                title="📅 Important Dates"
                items={highlights.dates}
                bgColor="#FFFBEB"
                borderColor="#FDE68A"
                iconBg="#FEF3C7"
                textColor="#92400E"
                badgeColor="#F59E0B"
              />
            )}
            {/* Obligations */}
            {highlights.obligations.length > 0 && (
              <HighlightCard
                title="⚡ Key Obligations"
                items={highlights.obligations}
                bgColor="#EFF6FF"
                borderColor="#BFDBFE"
                iconBg="#DBEAFE"
                textColor="#1E40AF"
                badgeColor="#3B82F6"
              />
            )}
            {/* Risks */}
            {highlights.risks.length > 0 && (
              <HighlightCard
                title="⚠️ Potential Risks"
                items={highlights.risks}
                bgColor="#FFF1F2"
                borderColor="#FECDD3"
                iconBg="#FFE4E6"
                textColor="#9F1239"
                badgeColor="#F43F5E"
              />
            )}
          </div>
        )}

        {/* Disclaimer */}
        {(highlights.dates.length > 0 || highlights.obligations.length > 0 || highlights.risks.length > 0) && (
          <p style={{
            fontSize: 13, color: "#94A3B8", fontFamily: "Georgia, serif",
            textAlign: "center", marginBottom: 20, fontStyle: "italic",
          }}>
            ⚖️ This is an AI-generated analysis. It may not be 100% accurate. Always consult a qualified lawyer for legal decisions.
          </p>
        )}

        <div style={{
          display: "grid",
          gridTemplateColumns: actions.length > 0 ? "1fr 380px" : "1fr",
          gap: 20, alignItems: "start",
        }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* ── SIMPLIFIED CONTENT ── */}
            <div style={{
              background: "#fff", borderRadius: 16, padding: 24,
              border: "1px solid #E2E8F0", boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
              animation: "fadeSlideUp 0.6s ease",
            }}>
              <div style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                marginBottom: 16,
              }}>
                <h3 style={{
                  fontFamily: "'Playfair Display', Georgia, serif",
                  fontWeight: 700, fontSize: 18, color: "#0F172A",
                  display: "flex", gap: 10, alignItems: "center",
                }}>
                  <span>📝</span> Simplified Content
                </h3>
                <button onClick={() => speakText(content, "content")} style={{
                  background: speakingId === "content" ? "#FEE2E2" : "#F1F5F9",
                  border: "1px solid " + (speakingId === "content" ? "#FCA5A5" : "#E2E8F0"),
                  color: speakingId === "content" ? "#DC2626" : "#64748B",
                  borderRadius: 8, padding: "5px 12px", cursor: "pointer",
                  fontSize: 12, fontWeight: 600, fontFamily: "Georgia, serif",
                  display: "flex", alignItems: "center", gap: 5, transition: "all 0.2s",
                }}>
                  {speakingId === "content" ? "⏹ Stop" : "🔊 Listen"}
                </button>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {contentParagraphs.map((paragraph, index) => (
                  <p key={`${index}-${paragraph.slice(0, 20)}`} style={{
                    fontSize: 16, color: "#374151", fontFamily: "Georgia, serif",
                    lineHeight: 1.7, padding: "12px 16px", borderRadius: 10,
                    background: "#F8FAFC", border: "1px solid #F1F5F9",
                  }}>{paragraph}</p>
                ))}
              </div>
            </div>
          </div>

          {actions.length > 0 && <ActionChecklistPanel actions={actions} />}
        </div>
      </div>

      {/* ── FLOATING CHATBOT ── */}
      <div style={{
        position: "fixed", bottom: 30, right: 30, zIndex: 1000,
        display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 16,
      }}>
        {/* Chat Drawer */}
        {showChat && (
          <div style={{
            width: 380, height: 500, background: "#fff", borderRadius: 20,
            boxShadow: "0 12px 48px rgba(0,0,0,0.15)", border: "1px solid #E2E8F0",
            display: "flex", flexDirection: "column", overflow: "hidden",
            animation: "fadeSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
          }}>
            <div style={{
              padding: "16px 20px", borderBottom: "1px solid #F1F5F9",
              background: "linear-gradient(135deg, #2563EB, #1D4ED8)",
              display: "flex", justifyContent: "space-between", alignItems: "center", color: "#fff",
            }}>
              <h3 style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontWeight: 700, fontSize: 17, display: "flex", gap: 8, alignItems: "center",
              }}>
                💬 NyayBot Assistant
              </h3>
              <button onClick={() => setShowChat(false)} style={{
                background: "rgba(255,255,255,0.2)", border: "none", color: "#fff",
                width: 28, height: 28, borderRadius: "50%", cursor: "pointer",
                fontSize: 16, display: "flex", alignItems: "center", justifyContent: "center",
              }}>×</button>
            </div>

            <div style={{ flex: 1, padding: "16px 20px", overflowY: "auto", background: "#F8FAFC" }}>
              {chatMessages.map((message, index) => (
                <div key={`${message.role}-${index}`} style={{
                  display: "flex",
                  justifyContent: message.role === "user" ? "flex-end" : "flex-start",
                  marginBottom: 12,
                }}>
                  {message.role === "ai" && (
                    <div style={{
                      width: 28, height: 28, borderRadius: "50%",
                      background: "#2563EB", display: "flex",
                      alignItems: "center", justifyContent: "center",
                      fontSize: 10, fontWeight: 700, color: "#fff",
                      flexShrink: 0, marginRight: 8, marginTop: 2,
                    }}>NB</div>
                  )}
                  <div style={{ maxWidth: "80%", display: "flex", flexDirection: "column", gap: 4 }}>
                    <div style={{
                      padding: "10px 14px",
                      borderRadius: message.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                      background: message.role === "user" ? "#2563EB" : "#fff",
                      boxShadow: message.role === "ai" ? "0 2px 4px rgba(0,0,0,0.05)" : "none",
                      fontSize: 13,
                      color: message.role === "user" ? "#fff" : "#1E293B",
                      fontFamily: "Georgia, serif", lineHeight: 1.5,
                      border: message.role === "ai" ? "1px solid #E2E8F0" : "none",
                    }}>
                      {message.loading ? (
                        <div style={{ display: "flex", gap: 3, padding: "4px 0" }}>
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#94A3B8", animation: "pulse 1s infinite 0.1s" }} />
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#94A3B8", animation: "pulse 1s infinite 0.2s" }} />
                          <div style={{ width: 6, height: 6, borderRadius: "50%", background: "#94A3B8", animation: "pulse 1s infinite 0.3s" }} />
                        </div>
                      ) : message.text}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            <div style={{ padding: "12px 16px", borderTop: "1px solid #F1F5F9", display: "flex", gap: 8, background: "#fff" }}>
              <input
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendChat()}
                placeholder="Ask something..."
                disabled={chatLoading}
                style={{
                  flex: 1, padding: "10px 14px", borderRadius: 12,
                  border: "1px solid #E2E8F0", fontSize: 13,
                  fontFamily: "Georgia, serif", outline: "none",
                }}
              />
              <button
                onClick={sendChat}
                disabled={chatLoading}
                style={{
                  width: 38, height: 38, borderRadius: 12,
                  background: "#2563EB", color: "#fff", border: "none",
                  cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
                }}
              >➤</button>
            </div>
          </div>
        )}

        {/* Floating Button */}
        <button
          onClick={() => setShowChat(!showChat)}
          style={{
            width: 60, height: 60, borderRadius: "50%",
            background: "linear-gradient(135deg, #2563EB, #1D4ED8)",
            color: "#fff", border: "none", cursor: "pointer",
            boxShadow: "0 8px 32px rgba(37, 99, 235, 0.4)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: 24, transition: "transform 0.3s ease",
            transform: showChat ? "rotate(180deg)" : "rotate(0)",
          }}
        >
          {showChat ? "×" : "💬"}
        </button>
      </div>
    </div>
  );
}

// ─── HIGHLIGHT CARD ─────────────────────────────────────────────────────────

function HighlightCard({ title, items, bgColor, borderColor, iconBg, textColor, badgeColor }) {
  return (
    <div style={{
      background: bgColor, borderRadius: 16, padding: 20,
      border: `1px solid ${borderColor}`,
      boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
    }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 8, marginBottom: 14,
      }}>
        <h4 style={{
          fontFamily: "'Playfair Display', Georgia, serif",
          fontWeight: 700, fontSize: 17, color: textColor,
        }}>{title}</h4>
        <span style={{
          background: badgeColor, color: "#fff", fontSize: 10,
          fontWeight: 800, padding: "2px 8px", borderRadius: 100,
        }}>{items.length}</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {items.map((item, i) => (
          <div key={i} style={{
            background: "rgba(255,255,255,0.7)", borderRadius: 10,
            padding: "10px 14px", border: `1px solid ${borderColor}`,
          }}>
            <p style={{
              fontSize: 15, color: textColor, fontFamily: "Georgia, serif",
              lineHeight: 1.5,
            }}>{item}</p>
          </div>
        ))}
      </div>
    </div>
  );
}


// ─── ACTION CHECKLIST ───────────────────────────────────────────────────────

function ActionChecklistPanel({ actions }) {
  const [items, setItems] = useState(
    actions.map((action) => ({
      text: typeof action === "string" ? action : action.text || action,
      done: false,
      deadline: typeof action === "object" ? action.deadline : null,
    }))
  );

  const toggle = (index) => {
    setItems((prev) =>
      prev.map((action, currentIndex) =>
        currentIndex === index ? { ...action, done: !action.done } : action
      )
    );
  };

  const completedCount = items.filter((action) => action.done).length;
  const progressPct = items.length ? (completedCount / items.length) * 100 : 0;

  return (
    <div style={{
      background: "#fff", borderRadius: 16, padding: 24,
      border: "1px solid #E2E8F0", boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
      animation: "fadeSlideUp 0.7s ease", position: "sticky", top: 80,
    }}>
      <h3 style={{
        fontFamily: "'Playfair Display', Georgia, serif",
        fontWeight: 700, fontSize: 18, color: "#0F172A",
        marginBottom: 4, display: "flex", gap: 10, alignItems: "center",
      }}>
        <span>✅</span> What You Should Do
      </h3>
      <p style={{ color: "#64748B", fontSize: 15, fontFamily: "Georgia, serif", marginBottom: 20 }}>
        {completedCount} of {items.length} steps completed
      </p>

      <div style={{
        background: "#F1F5F9", borderRadius: 100, height: 6,
        marginBottom: 24, overflow: "hidden",
      }}>
        <div style={{
          height: "100%", borderRadius: 100,
          background: "linear-gradient(90deg, #22C55E, #4ADE80)",
          width: `${progressPct}%`, transition: "width 0.4s ease",
        }} />
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {items.map((action, index) => (
          <div
            key={`${action.text}-${index}`} onClick={() => toggle(index)}
            style={{
              display: "flex", gap: 12, alignItems: "flex-start",
              padding: "12px 14px", borderRadius: 12, cursor: "pointer",
              background: action.done ? "#F0FDF4" : "#FAFAFA",
              border: `1px solid ${action.done ? "#BBF7D0" : "#F1F5F9"}`,
              transition: "all 0.2s",
            }}
          >
            <div style={{
              width: 22, height: 22, borderRadius: 6, flexShrink: 0,
              border: `2px solid ${action.done ? "#22C55E" : "#CBD5E1"}`,
              background: action.done ? "#22C55E" : "#fff",
              display: "flex", alignItems: "center", justifyContent: "center",
              transition: "all 0.2s", marginTop: 1,
            }}>
              {action.done && <span style={{ color: "#fff", fontSize: 10, fontWeight: 700 }}>✓</span>}
            </div>
            <div style={{ flex: 1 }}>
              <p style={{
                fontSize: 15, fontFamily: "Georgia, serif", lineHeight: 1.5,
                color: action.done ? "#166534" : "#374151",
                textDecoration: action.done ? "line-through" : "none",
              }}>{action.text}</p>
              {action.deadline && (
                <div style={{
                  display: "inline-flex", alignItems: "center", gap: 4,
                  marginTop: 4, background: "#FFF7ED", border: "1px solid #FED7AA",
                  borderRadius: 6, padding: "2px 8px",
                }}>
                  <span style={{ fontSize: 10, fontWeight: 700 }}>Due</span>
                  <span style={{
                    fontSize: 11, color: "#C2410C", fontWeight: 600, fontFamily: "Georgia, serif",
                  }}>{action.deadline}</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
