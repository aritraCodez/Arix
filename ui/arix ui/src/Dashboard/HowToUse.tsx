import { Button } from "@/Components/ui/button";
import { Link } from "react-router-dom";
import { HelpCircle, ArrowLeft, Download, Settings, PlayCircle, ShieldCheck } from "lucide-react";
import { Card, CardHeader, CardTitle } from "@/Components/ui/card";

export default function HowToUse() {
  const steps = [
    {
      title: "Download & Extract",
      desc: "Click the download button on the homepage to get the .zip file. Extract it to a folder on your computer.",
      icon: <Download className="w-6 h-6 text-purple-400" />
    },
    {
      title: "Enable Developer Mode",
      desc: "Go to chrome://extensions in your browser and toggle 'Developer mode' in the top right corner.",
      icon: <Settings className="w-6 h-6 text-blue-400" />
    },
    {
      title: "Load Unpacked",
      desc: "Click 'Load unpacked' and select the folder where you extracted the extension files.",
      icon: <PlayCircle className="w-6 h-6 text-emerald-400" />
    },
    {
      title: "Start Trading",
      desc: "Open your trading platform Quotex. The Arix panel will automatically inject into the side.",
      icon: <ShieldCheck className="w-6 h-6 text-pink-400" />
    }
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white selection:bg-purple-500/30">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] bg-blue-900/10 blur-[120px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-4xl mx-auto px-6 py-20">
        <Link to="/">
          <Button variant="ghost" className="mb-8 text-gray-400 hover:text-black">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
          </Button>
        </Link>

        <div className="flex items-center gap-4 mb-12">
          <div className="p-3 rounded-2xl bg-blue-500/10 border border-blue-500/20">
            <HelpCircle className="w-8 h-8 text-blue-400" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">How to Use Arix</h1>
        </div>

        <div className="grid gap-6 mb-12">
          {steps.map((step, idx) => (
            <Card key={idx} className="bg-white/[0.03] border-white/10 overflow-hidden hover:bg-white/[0.05] transition-all duration-300">
              <div className="flex flex-col md:flex-row">
                <div className="p-6 flex items-center justify-center bg-white/[0.02] border-r border-white/5 md:w-24">
                  <span className="text-3xl font-black text-white/10">{idx + 1}</span>
                </div>
                <CardHeader className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {step.icon}
                    <CardTitle className="text-white text-xl">{step.title}</CardTitle>
                  </div>
                  <p className="text-gray-400 leading-relaxed">
                    {step.desc}
                  </p>
                </CardHeader>
              </div>
            </Card>
          ))}
        </div>

        <Card className="bg-white/[0.03] border-white/10 overflow-hidden mb-12">
          <CardHeader>
            <div className="flex items-center gap-3 mb-4">
              <PlayCircle className="w-6 h-6 text-purple-400" />
              <CardTitle className="text-white text-2xl">Live Trading Demonstration</CardTitle>
            </div>
            <p className="text-gray-400 leading-relaxed mb-6">
              Watch Arix in action. In this demonstration, I made two trades using this prediction bot — one resulted in a loss, and the other was a win, showcasing the realistic performance and real-time signal generation of the system.
            </p>
            <div className="relative rounded-xl overflow-hidden border border-white/10 bg-black/50 aspect-video">
              <video 
                className="w-full h-full object-cover" 
                controls 
                autoPlay 
                muted 
                loop
                playsInline
              >
                <source src="/demo.mp4" type="video/mp4" />
                Your browser does not support the video tag.
              </video>
            </div>
          </CardHeader>
        </Card>
      </div>
    </div>
  );
}
