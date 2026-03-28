// src/App.jsx

import { useState, useCallback } from "react";
import "./styles/global.css";

import Navbar from "./components/Navbar";
import LandingHero from "./components/LandingHero";
import UploadBox from "./components/UploadBox";
import FilePreview from "./components/FilePreview";
import ProcessingLoader from "./components/ProcessingLoader";
import OutputDashboard from "./components/OutputDashboard";

// Stage machine: landing → upload → preview → processing → output
export default function App() {
  const [stage, setStage] = useState("landing");
  const [file, setFile] = useState(null);
  const [lang, setLang] = useState("en");
  const [apiData, setApiData] = useState(null);

  const reset = useCallback(() => {
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
