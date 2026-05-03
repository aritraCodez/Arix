import { useState } from 'react';
import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { Link } from 'react-router-dom';
import { Button } from "@/Components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/Components/ui/card";
import { Badge } from "@/Components/ui/badge";
import { Download, Zap, Brain, Shield, Target, Cpu, CheckCircle2 } from "lucide-react";

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

const FEATURES = [
  {
    title: "LSTM Deep Learning",
    desc: "Proprietary Long Short-Term Memory (LSTM) neural networks trained on millions of data points for precise 1m predictions.",
    icon: <Brain className="w-8 h-8 text-purple-400" />,
  },
  {
    title: "Mathematical Edge",
    desc: "Sophisticated quantitative algorithms and statistical models that strip away market noise for clear entry signals.",
    icon: <Zap className="w-8 h-8 text-yellow-400" />,
  },
  {
    title: "Real-Time AI Analysis",
    desc: "Live stream processing combining ML predictions with traditional technical indicators in under 500ms.",
    icon: <Cpu className="w-8 h-8 text-pink-400" />,
  },
  {
    title: "Zero API Keys",
    desc: "Completely free data fetching from Binance and Yahoo Finance with no account or keys needed.",
    icon: <Shield className="w-8 h-8 text-green-400" />,
  },
  {
    title: "Auto Asset Detection",
    desc: "Automatically identifies your active chart on Quotex and switches its ML model in real-time.",
    icon: <Target className="w-8 h-8 text-blue-400" />,
  },
  {
    title: "Chrome Native",
    desc: "Lightweight extension architecture that runs entirely in your browser with zero performance lag.",
    icon: <CheckCircle2 className="w-8 h-8 text-emerald-400" />,
  }
];

export default function HomePage() {
  const [isZipping, setIsZipping] = useState(false);
  const [status, setStatus] = useState('');

  const downloadExtension = async () => {
    setIsZipping(true);
    setStatus('Preparing files...');
    const zip = new JSZip();

    try {
      for (const filePath of EXTENSION_FILES) {
        setStatus(`Adding ${filePath}...`);
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
    <div className="min-h-screen bg-[#0a0a0c] text-white selection:bg-purple-500/30">
      {/* Background Glow */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-purple-900/20 blur-[120px] rounded-full" />
        <div className="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-900/20 blur-[120px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-12">
        {/* Header/Nav */}
        <nav className="flex justify-between items-center mb-16">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20">
              <span className="font-bold text-xl">A</span>
            </div>
            <span className="text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              Arix Intelligence
            </span>
          </div>
          <div className="flex items-center gap-4">
            <a 
              href="https://github.com/aritraCodez/Arix" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-gray-400 hover:text-white transition-colors"
              title="View on GitHub"
            >
              <svg 
                viewBox="0 0 24 24" 
                className="w-6 h-6 fill-current" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
            </a>
            <Badge variant="outline" className="border-purple-500/50 text-purple-400 bg-purple-500/10 px-3 py-1">
              v1.1.1 Stable
            </Badge>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="text-center mb-24">
          <h1 className="text-5xl md:text-7xl font-extrabold mb-6 tracking-tight leading-tight">
            The Ultimate Real-Time <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-blue-400 to-emerald-400">
              Trading Companion
            </span>
          </h1>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Advanced **LSTM neural networks** and **mathematical models** 
            injected directly into Quotex. 500ms latency, zero API keys.
          </p>

          <Card className="max-w-md mx-auto bg-white/5 border-white/10 backdrop-blur-xl shadow-2xl overflow-hidden">
            <CardHeader className="pb-4">
              <CardTitle className="text-white text-xl">Get Started Now</CardTitle>
              <CardDescription className="text-gray-400">Download the extension and elevate your trading.</CardDescription>
            </CardHeader>
            <CardContent>
              <Button 
                onClick={downloadExtension}
                disabled={isZipping}
                size="lg"
                className="w-full h-14 text-lg font-bold bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 border-none shadow-lg shadow-purple-500/25 transition-all duration-300 active:scale-[0.98]"
              >
                {isZipping ? (
                  <span className="flex items-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Processing...
                  </span>
                ) : (
                  <span className="flex items-center gap-2">
                    <Download className="w-5 h-5" />
                    Download Extension (.zip)
                  </span>
                )}
              </Button>
              {status && (
                <p className="mt-4 text-sm font-medium text-purple-400 animate-pulse">
                  {status}
                </p>
              )}
            </CardContent>
           
          </Card>
        </section>

        {/* Features Grid */}
        <section className="mb-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Powerful Features</h2>
            <div className="w-20 h-1 bg-gradient-to-r from-purple-600 to-blue-600 mx-auto rounded-full" />
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((feature, idx) => (
              <Card key={idx} className="bg-white/[0.03] border-white/10 hover:bg-white/[0.06] hover:border-white/20 transition-all duration-300 group">
                <CardHeader>
                  <div className="mb-4 p-3 w-fit rounded-2xl bg-white/5 group-hover:bg-white/10 transition-colors">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-white text-xl group-hover:text-purple-400 transition-colors">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-400 leading-relaxed">
                    {feature.desc}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="border-t border-white/10 pt-12 text-center">
          <div className="flex justify-center gap-8 mb-8 text-gray-500">
            <Link to="/how-to-use" className="hover:text-purple-400 transition-colors">How to Use</Link>
            <Link to="/privacy" className="hover:text-purple-400 transition-colors">Privacy Policy</Link>
            <a href="https://github.com/aritraCodez/Arix" target="_blank" rel="noopener noreferrer" className="hover:text-purple-400 transition-colors">GitHub Repository</a>
          </div>
          <p className="text-gray-600 text-sm">
            &copy; {new Date().getFullYear()} Arix Intelligence. All rights reserved. <br />
            <span className="text-gray-700 italic mt-2 block">For educational and research purposes only. Trading involves risk.</span>
          </p>
        </footer>
      </div>
    </div>
  );
}
