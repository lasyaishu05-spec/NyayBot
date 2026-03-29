// src/App.jsx

import { useState, useCallback, useEffect } from "react";
import "./styles/global.css";

import Navbar from "./components/Navbar";
import LandingHero from "./components/LandingHero";
import UploadBox from "./components/UploadBox";
import FilePreview from "./components/FilePreview";
import ProcessingLoader from "./components/ProcessingLoader";
import OutputDashboard from "./components/OutputDashboard";

// Stage machine: landing → upload → preview → processing → output
export default function App() {
  const [stage, setStage] = useState(() => {
    const saved = localStorage.getItem("nyaybot_session");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.stage === "output") return "output";
      } catch (e) {}
    }
    return "landing";
  });
  
  const [file, setFile] = useState(() => {
    const saved = localStorage.getItem("nyaybot_session");
    return saved ? JSON.parse(saved).file || null : null;
  });
  
  const [lang, setLang] = useState(() => {
    const saved = localStorage.getItem("nyaybot_session");
    return saved ? JSON.parse(saved).lang || "en" : "en";
  });
  
  const [apiData, setApiData] = useState(() => {
    const saved = localStorage.getItem("nyaybot_session");
    return saved ? JSON.parse(saved).apiData || null : null;
  });

  // Save session to local database
  useEffect(() => {
    if (stage === "output" && apiData) {
      localStorage.setItem("nyaybot_session", JSON.stringify({ stage, file, lang, apiData }));
    }
  }, [stage, file, lang, apiData]);
  
  // Force scroll to top on every stage change
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [stage]);

  const reset = useCallback(() => {
    localStorage.removeItem("nyaybot_session");
    localStorage.removeItem("nyaybot_chat");
    setStage("landing");
    setFile(null);
    setLang("en");
    setApiData(null);
  }, []);

  return (
    <>
      <Navbar onReset={reset} />

      {stage === "landing" && (
        <LandingHero onGetStarted={() => setStage("upload")} />
      )}

      {stage === "upload" && (
        <UploadBox
          onFileSelected={(f) => { setFile(f); setStage("preview"); }}
        />
      )}

      {stage === "preview" && file && (
        <FilePreview
          file={file}
          lang={lang}
          setLang={setLang}
          onProcess={() => setStage("processing")}
          onRemove={() => setStage("upload")}
        />
      )}

      {stage === "processing" && (
        <ProcessingLoader
          file={file}
          lang={lang}
          onDone={(data) => { setApiData(data); setStage("output"); }}
        />
      )}

      {stage === "output" && (
        <OutputDashboard file={file} lang={lang} apiData={apiData} onReset={reset} />
      )}
    </>
  );
}
