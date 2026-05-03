import { useState } from 'react';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import './App.css';

const EXTENSION_FILES = [
  'config.js',
  'manifest.json',
  'background/service-worker.js',
  'content/content.js',
  'content/panel.css',
  'icons/icon16.png',
  'icons/icon48.png',
  'icons/icon128.png',
  'popup/popup.html',
  'popup/popup.js'
];

function App() {
  const [isZipping, setIsZipping] = useState(false);
  const [status, setStatus] = useState('');

  const downloadExtension = async () => {
    setIsZipping(true);
    setStatus('Preparing files...');
    const zip = new JSZip();

    try {
      for (const filePath of EXTENSION_FILES) {
        setStatus(`Adding ${filePath}...`);
        // Fetch from the public/extension folder
        const response = await fetch(`/extension/${filePath}`);
        if (!response.ok) throw new Error(`Failed to fetch ${filePath}`);
        
        const blob = await response.blob();
        zip.file(filePath, blob);
      }

      setStatus('Generating ZIP...');
      const content = await zip.generateAsync({ type: 'blob' });
      
      setStatus('Saving...');
      saveAs(content, 'arix-signal-analyzer.zip');
      
      setStatus('Download complete!');
      setTimeout(() => setStatus(''), 3000);
    } catch (error) {
      console.error('Error creating ZIP:', error);
      setStatus('Error: Could not create ZIP file.');
    } finally {
      setIsZipping(false);
    }
  };

  return (
    <div className="app-container">
      <header className="hero-section">
        <h1 className="hero-title">Arix Signal Analyzer</h1>
        <p className="hero-subtitle">
          The ultimate real-time trading companion. Professional technical analysis 
          and AI-powered predictions, injected directly into your trading platform.
        </p>

        <div className="download-card">
          <button 
            className="btn-download" 
            onClick={downloadExtension}
            disabled={isZipping}
          >
            <span className="feature-icon" style={{margin:0}}>📦</span>
            {isZipping ? 'Processing...' : 'Download Extension (.zip)'}
          </button>
          {status && <p className="status-text">{status}</p>}
          <p style={{ marginTop: '20px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Latest Version: v1.1.0 • No Setup Required
          </p>
        </div>
      </header>

      <div className="features-grid">
        <div className="feature-card">
          <div className="feature-icon">⚡</div>
          <h3 className="feature-title">500ms Real-Time</h3>
          <p className="feature-desc">Ultra-low latency signal polling ensures you never miss a market move.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🧠</div>
          <h3 className="feature-title">LSTM Intelligence</h3>
          <p className="feature-desc">Proprietary deep learning model trained on historical market data for 1-minute predictions.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🛡️</div>
          <h3 className="feature-title">Zero API Keys</h3>
          <p className="feature-desc">Completely free data fetching from Binance and Yahoo Finance with no account needed.</p>
        </div>
        <div className="feature-card">
          <div className="feature-icon">🎯</div>
          <h3 className="feature-title">Asset Detection</h3>
          <p className="feature-desc">Automatically identifies what you're trading and switches analysis in real-time.</p>
        </div>
      </div>

      <footer>
        &copy; {new Date().getFullYear()} Arix Intelligence. For educational purposes only.
      </footer>
    </div>
  );
}

export default App;
