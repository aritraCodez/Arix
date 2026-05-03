import { Button } from "@/Components/ui/button";
import { Link } from "react-router-dom";
import { Shield, ArrowLeft } from "lucide-react";

export default function Privacy() {
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-white selection:bg-purple-500/30">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-purple-900/10 blur-[120px] rounded-full" />
      </div>

      <div className="relative z-10 max-w-3xl mx-auto px-6 py-20">
        <Link to="/">
          <Button variant="ghost" className="mb-8 text-gray-400 hover:text-black">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Home
          </Button>
        </Link>

        <div className="flex items-center gap-4 mb-8">
          <div className="p-3 rounded-2xl bg-purple-500/10 border border-purple-500/20">
            <Shield className="w-8 h-8 text-purple-400" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">Privacy Policy</h1>
        </div>

        <div className="space-y-8 text-gray-400 leading-relaxed">
          <section>
            <h2 className="text-xl font-semibold text-white mb-4">Your Privacy Matters</h2>
            <p>
              Arix Intelligence is committed to protecting your personal data. This Privacy Policy explains how we collect, use, and safeguard your information when you use our extension.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">Data Collection</h2>
            <p>
              We do **not** collect any personally identifiable information (PII). Our extension operates locally on your machine. We only fetch public market data from APIs like Binance and Yahoo Finance to provide trading signals.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">No Data Selling</h2>
            <p>
              We never sell, trade, or otherwise transfer your information to outside parties. Your trading history and preferences remain on your device and are never uploaded to our servers.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">Third-Party Services</h2>
            <p>
              The extension interacts with trading platforms Quotex and market data providers. Please refer to their respective privacy policies regarding how they handle data on their platforms.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-white mb-4">Changes to This Policy</h2>
            <p>
              We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page.
            </p>
          </section>

          <footer className="pt-12 border-t border-white/10 text-sm italic">
            Last updated: May 3, 2026
          </footer>
        </div>
      </div>
    </div>
  );
}
