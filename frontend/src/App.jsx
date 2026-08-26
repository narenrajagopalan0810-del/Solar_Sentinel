import React, { useState, useEffect } from 'react';
import { 
  checkHealth, fetchSamplePresets, fetchSampleImageBlob, 
  analyzeSonarImage 
} from './services/api';

import Header from './components/Header';
import MetricCards from './components/MetricCards';
import PresetSelector from './components/PresetSelector';
import TelemetryControl from './components/TelemetryControl';
import SonarViewer from './components/SonarViewer';
import DetectionInspector from './components/DetectionInspector';
import MaritimeMap from './components/MaritimeMap';
import ReportModal from './components/ReportModal';
import { AlertCircle } from 'lucide-react';

export default function App() {
  const [systemHealth, setSystemHealth] = useState(null);
  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState(null);
  
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState('');
  
  const [telemetry, setTelemetry] = useState({
    vessel_lat: 13.0827,
    vessel_lon: 80.2707,
    heading: 85.0,
    altitude: 18.0,
    swath_width_m: 100.0,
    mission_name: 'MoES-Survey-Alpha'
  });

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [selectedDetection, setSelectedDetection] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);

  // 1. Initial Health & Presets Fetch
  useEffect(() => {
    const initSystem = async () => {
      try {
        const health = await checkHealth();
        setSystemHealth(health);
      } catch (err) {
        console.warn('Backend connection error:', err);
      }

      try {
        const sampleList = await fetchSamplePresets();
        setPresets(sampleList);
        // Auto-select first preset for instant out-of-the-box delight
        if (sampleList && sampleList.length > 0) {
          handlePresetSelect(sampleList[0]);
        }
      } catch (err) {
        console.warn('Could not fetch preset scenarios:', err);
      }
    };

    initSystem();
  }, []);

  // 2. Preset Selection Handler
  const handlePresetSelect = async (preset) => {
    setSelectedPreset(preset);
    setErrorMessage('');
    if (preset.nav) {
      setTelemetry((prev) => ({
        ...prev,
        ...preset.nav,
      }));
    }

    try {
      const blob = await fetchSampleImageBlob(preset.filename);
      const sampleFile = new File([blob], preset.filename, { type: 'image/png' });
      setFile(sampleFile);
      setPreviewUrl(URL.createObjectURL(sampleFile));
    } catch (err) {
      console.error('Failed to load sample image blob:', err);
    }
  };

  // 3. File Input Handler
  const handleFileChange = (newFile) => {
    setFile(newFile);
    setSelectedPreset(null);
    setErrorMessage('');
    if (newFile) {
      setPreviewUrl(URL.createObjectURL(newFile));
    } else {
      setPreviewUrl('');
    }
  };

  // 4. Run Sonar Analysis
  const handleRunAnalysis = async () => {
    if (!file) {
      setErrorMessage('Please upload a sonar image or select a quick-demo scenario.');
      return;
    }

    setIsAnalyzing(true);
    setErrorMessage('');

    const formData = new FormData();
    formData.append('file', file);
    formData.append('vessel_lat', telemetry.vessel_lat);
    formData.append('vessel_lon', telemetry.vessel_lon);
    formData.append('heading', telemetry.heading);
    formData.append('altitude', telemetry.altitude);
    formData.append('swath_width_m', telemetry.swath_width_m);
    formData.append('mission_name', telemetry.mission_name || 'MoES-Survey');

    try {
      const result = await analyzeSonarImage(formData);
      setAnalysisResult(result);
      if (result.detections && result.detections.length > 0) {
        setSelectedDetection(result.detections[0]);
      } else {
        setSelectedDetection(null);
      }
    } catch (err) {
      console.error('Analysis failed:', err);
      setErrorMessage(
        err.response?.data?.message || err.message || 'Sonar analysis failed. Check backend connection.'
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  // 5. Reset Handler
  const handleReset = () => {
    setFile(null);
    setPreviewUrl('');
    setAnalysisResult(null);
    setSelectedDetection(null);
    setSelectedPreset(null);
    setErrorMessage('');
  };

  return (
    <div className="min-h-screen flex flex-col bg-sonar-950 text-slate-100">
      {/* HUD Header */}
      <Header
        systemHealth={systemHealth}
        analysisResult={analysisResult}
        onOpenReport={() => setIsReportModalOpen(true)}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-6 space-y-4">
        {/* Quick Demo Preset Selector */}
        <PresetSelector
          presets={presets}
          selectedPreset={selectedPreset}
          onSelectPreset={handlePresetSelect}
          disabled={isAnalyzing}
        />

        {/* Error Notification Banner */}
        {errorMessage && (
          <div className="bg-rose-950/60 border border-rose-500/50 rounded-lg p-3 flex items-center gap-3 text-xs font-mono text-rose-200">
            <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
            <div className="flex-1">{errorMessage}</div>
            <button
              onClick={() => setErrorMessage('')}
              className="text-slate-400 hover:text-white"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* KPI Metrics Summary Row */}
        <MetricCards
          summary={analysisResult?.summary}
          processingTimeMs={analysisResult?.processing_time_ms}
          missionId={analysisResult?.mission_id}
        />

        {/* 2-Column Tactical Intelligence Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left Column (5 Cols): Ingestion Telemetry + Inspection Details */}
          <div className="lg:col-span-5 space-y-4">
            <TelemetryControl
              file={file}
              previewUrl={previewUrl}
              telemetry={telemetry}
              isAnalyzing={isAnalyzing}
              onFileChange={handleFileChange}
              onTelemetryChange={setTelemetry}
              onAnalyze={handleRunAnalysis}
              onReset={handleReset}
            />

            <DetectionInspector
              detection={selectedDetection}
              vesselPos={telemetry}
            />
          </div>

          {/* Right Column (7 Cols): Sonar Visualizer + GIS Maritime Map */}
          <div className="lg:col-span-7 space-y-4">
            <SonarViewer
              analysisResult={analysisResult}
              selectedDetection={selectedDetection}
              onSelectDetection={setSelectedDetection}
              isAnalyzing={isAnalyzing}
            />

            <MaritimeMap
              vesselNav={analysisResult ? analysisResult.navigation : telemetry}
              detections={analysisResult?.detections || []}
              selectedDetection={selectedDetection}
              onSelectDetection={setSelectedDetection}
            />
          </div>
        </div>
      </main>

      {/* Mission Intelligence Report Modal */}
      <ReportModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        analysisResult={analysisResult}
      />

      {/* Footer */}
      <footer className="mt-8 py-4 border-t border-sonar-800/80 text-center font-mono text-[11px] text-slate-500">
        SonarSentinel Maritime Defense & Ocean Floor Intelligence • Ministry of Earth Sciences (MoES) Problem SIH26057 • Smart India Hackathon
      </footer>
    </div>
  );
}
