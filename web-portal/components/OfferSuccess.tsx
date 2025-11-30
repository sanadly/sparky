import React from 'react';
import { CheckCircle, Copy, FileText } from 'lucide-react';

interface OfferSuccessProps {
  offerId: string;
  productName: string;
  onReset: () => void;
}

const OfferSuccess: React.FC<OfferSuccessProps> = ({ offerId, productName, onReset }) => {
  const copyToClipboard = () => {
    navigator.clipboard.writeText(offerId);
  };

  return (
    <div className="w-full max-w-sm mx-auto animate-scale-in">
      <div className="bg-gradient-to-br from-green-500/20 to-teal-500/20 backdrop-blur-xl border border-green-500/30 rounded-2xl p-6 text-center relative overflow-hidden">
        {/* Background Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 bg-green-500/20 blur-[50px] rounded-full" />

        <div className="relative z-10 flex flex-col items-center">
          <div className="w-16 h-16 bg-gradient-to-br from-green-400 to-teal-500 rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(74,222,128,0.4)] mb-4 animate-bounce-small">
            <CheckCircle className="text-white w-8 h-8" />
          </div>

          <h2 className="text-xl font-bold text-white mb-1">Angebot erstellt!</h2>
          <p className="text-gray-300 text-sm mb-6">Dein Vertrag ist vorbereitet.</p>

          <div className="w-full bg-black/20 rounded-xl p-4 mb-4 border border-white/5">
            <div className="flex items-center gap-2 mb-2 text-gray-400 text-xs uppercase tracking-wider font-semibold">
              <FileText size={12} />
              Produkt
            </div>
            <div className="text-white font-medium text-lg mb-4">{productName}</div>

            <div className="flex items-center gap-2 mb-2 text-gray-400 text-xs uppercase tracking-wider font-semibold">
              <Copy size={12} />
              Angebotsnummer
            </div>
            <button 
              onClick={copyToClipboard}
              className="w-full bg-black/30 hover:bg-black/40 transition-colors rounded-lg p-2 flex items-center justify-between group cursor-pointer border border-white/5"
            >
              <code className="text-green-400 font-mono text-sm">{offerId}</code>
              <Copy size={14} className="text-gray-500 group-hover:text-white transition-colors" />
            </button>
          </div>
          
          <p className="text-gray-400 text-xs text-center mb-4 px-2">
            In einem echten Szenario würden Sie diese Nummer verwenden, um den Vertrag zu unterschreiben, sie beim Support anzugeben, oder sie könnte eine E-Mail mit den Vertragsdetails auslösen.
          </p>

          <button 
            onClick={onReset}
            className="w-full py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-medium transition-all border border-white/10"
          >
            Neuen Chat starten
          </button>
        </div>
      </div>
    </div>
  );
};

export default OfferSuccess;
