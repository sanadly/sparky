import React, { useEffect, useState } from 'react';
import { Product } from '../types';
import { Leaf, Zap, Check } from 'lucide-react';
import { generateProductPitch } from '../services/geminiService';
import ReactMarkdown from 'react-markdown';

interface Props {
  product: Product;
  userConsumption: number;
  onSelect: (product: Product) => void;
  isSelected?: boolean;
}

const ProductCard: React.FC<Props> = ({ product, userConsumption, onSelect, isSelected }) => {
  const [pitch, setPitch] = useState<string>('Analysiere Kompatibilität...');

  useEffect(() => {
    let isMounted = true;
    generateProductPitch(product, userConsumption).then(text => {
      if (isMounted) setPitch(text);
    });
    return () => { isMounted = false; };
  }, [product, userConsumption]);

  return (
    <div 
      className={`
        relative min-w-[280px] w-[280px] p-5 rounded-2xl transition-all duration-300 snap-center
        flex flex-col justify-between h-[420px] cursor-pointer group
        ${isSelected 
          ? 'bg-gradient-to-br from-teal-900/80 to-blue-900/80 border-2 border-energy-teal shadow-[0_0_20px_rgba(100,255,218,0.3)]' 
          : 'bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/30'}
      `}
      onClick={() => onSelect(product)}
    >
      {/* Selection Indicator */}
      {isSelected && (
        <div className="absolute -top-3 -right-3 bg-energy-teal text-energy-900 rounded-full p-1 shadow-lg z-10">
          <Check size={20} strokeWidth={3} />
        </div>
      )}

      {/* Header */}
      <div>
        <div className="flex justify-between items-start mb-4">
          <div className={`p-2 rounded-lg ${product.isGreen ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-400'}`}>
            {product.isGreen ? <Leaf size={24} /> : <Zap size={24} />}
          </div>
          <span className="text-xs font-mono text-gray-400 bg-black/20 px-2 py-1 rounded">
            {product.contractDuration} Monate
          </span>
        </div>
        
        <h4 className="text-xl font-bold text-white mb-2 leading-tight">{product.name}</h4>
        
        {/* Gemini Generated Pitch */}
        {/* Gemini Generated Pitch */}
        <div className="mb-4 min-h-[60px]">
           <div className="text-xs text-gray-300 bg-white/5 p-3 rounded-xl border border-white/5 leading-relaxed">
              <ReactMarkdown
                  components={{
                      p: ({node, ...props}) => <p className="m-0" {...props} />,
                      strong: ({node, ...props}) => <span className="text-energy-teal font-bold" {...props} />
                  }}
              >
                  {pitch}
              </ReactMarkdown>
           </div>
        </div>
      </div>

      {/* Pricing Visuals */}
      <div className="space-y-4">
        {(product.basePrice > 0 || product.workingPrice > 0) ? (
          <>
            <div className="bg-black/20 p-3 rounded-lg flex justify-between items-center backdrop-blur-sm">
              <span className="text-sm text-gray-400">Grundpreis</span>
              <span className="font-mono text-white">{(product.basePrice || 0).toFixed(2)}€<span className="text-xs text-gray-500">/Jahr</span></span>
            </div>
            <div className="bg-black/20 p-3 rounded-lg flex justify-between items-center backdrop-blur-sm">
              <span className="text-sm text-gray-400">Arbeitspreis</span>
              <span className="font-mono text-white">{(product.workingPrice || 0).toFixed(2)}<span className="text-xs text-gray-500">ct/kWh</span></span>
            </div>
          </>
        ) : (
          <div className="bg-black/20 p-4 rounded-lg flex flex-col items-center justify-center backdrop-blur-sm h-[108px]">
             <span className="text-sm text-gray-400 mb-1">Geschätzte Kosten</span>
             <span className="font-mono text-2xl text-white font-bold">{(product.totalPrice || 0).toFixed(2)} €</span>
             <span className="text-xs text-gray-500">pro Jahr (bei 2500 kWh)</span>
          </div>
        )}
      </div>

      {/* Action Area */}
      <div className="mt-4 pt-4 border-t border-white/10">
          <div className="text-center text-xs text-gray-400 mb-2">Zum Simulieren tippen</div>
          <div className={`w-full h-1 rounded-full ${isSelected ? 'bg-energy-teal' : 'bg-white/20 group-hover:bg-white/40'}`} />
      </div>
    </div>
  );
};

export default ProductCard;