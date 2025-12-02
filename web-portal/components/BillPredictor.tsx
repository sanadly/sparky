import React, { useEffect, useState } from 'react';
import { Product, SimulationResult } from '../types';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface Props {
  product: Product;
  consumption: number;
  onSecure: () => void;
}

const BillPredictor: React.FC<Props> = ({ product, consumption, onSecure }) => {
  const [count, setCount] = useState(0);
  const [simulation, setSimulation] = useState<SimulationResult | null>(null);

  useEffect(() => {
    // Simulate Backend Calculation
    const baseCost = product.basePrice;
    // Convert cents to EUR
    const usageCost = (consumption * product.workingPrice) / 100; 
    const total = baseCost + usageCost;

    setSimulation({
      netAmount: total,
      currency: 'EUR',
      breakdown: { baseCost, usageCost }
    });
  }, [product, consumption]);

  // Count up animation
  useEffect(() => {
    if (!simulation) return;
    
    const duration = 1500; // ms
    const steps = 60;
    const increment = simulation.netAmount / steps;
    let current = 0;
    
    const timer = setInterval(() => {
      current += increment;
      if (current >= simulation.netAmount) {
        setCount(simulation.netAmount);
        clearInterval(timer);
      } else {
        setCount(current);
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [simulation]);

  if (!simulation) return <div className="p-4 text-center text-energy-teal animate-pulse">Berechne Angebot...</div>;

  const data = [
    { name: 'Grundpreis', value: simulation.breakdown.baseCost },
    { name: 'Verbrauch', value: simulation.breakdown.usageCost },
  ];
  const COLORS = ['#233554', '#64ffda'];

  return (
    <div className="w-full max-w-sm mx-auto bg-gradient-to-b from-energy-800 to-energy-900 rounded-3xl p-6 shadow-2xl border border-white/10 animate-slide-up relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-32 bg-energy-teal/10 blur-[60px] rounded-full pointer-events-none" />

      <h3 className="text-center text-energy-teal font-bold tracking-wide mb-1 uppercase text-sm">Preis-Vorschau</h3>
      <p className="text-center text-white font-medium text-lg mb-6">{product.name}</p>

      {/* Main Counter (Total Year) */}
      <div className="flex flex-col items-center justify-center mb-8 relative">
        <div className="text-5xl font-bold text-white z-10 font-mono tracking-tighter tabular-nums drop-shadow-lg">
          {count.toFixed(2)}
          <span className="text-2xl text-energy-teal ml-1">€</span>
        </div>
        <div className="text-xs text-gray-400 mt-1 font-medium tracking-wide">
            voraussichtl. pro Jahr
        </div>
      </div>

      {/* Breakdown */}
      <div className="space-y-4 mb-8">
          {/* Base Price Row */}
          <div className="flex justify-between items-end border-b border-white/5 pb-2">
              <div className="flex flex-col">
                  <span className="text-gray-400 text-xs uppercase tracking-wider mb-1">Grundpreis</span>
                  <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#233554]" />
                      <span className="text-white font-medium">Basis</span>
                  </div>
              </div>
              <span className="font-mono text-white text-lg">{simulation.breakdown.baseCost.toFixed(2)} €</span>
          </div>

          {/* Usage Price Row */}
          <div className="flex justify-between items-end border-b border-white/5 pb-2">
              <div className="flex flex-col">
                  <span className="text-gray-400 text-xs uppercase tracking-wider mb-1">Verbrauch ({consumption} kWh)</span>
                  <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#64ffda]" />
                      <span className="text-white font-medium">Arbeitspreis</span>
                  </div>
              </div>
              <span className="font-mono text-white text-lg">{simulation.breakdown.usageCost.toFixed(2)} €</span>
          </div>
          
          <div className="text-[10px] text-gray-500 text-right">
              Basis: {product.workingPrice.toFixed(2)} ct/kWh
          </div>
      </div>

      {/* Monthly Average Highlight */}
      <div className="mb-8 bg-white/5 rounded-2xl p-4 border border-white/10 flex items-center justify-between backdrop-blur-sm">
          <div className="flex items-center gap-3">
              <div className="p-2 bg-energy-teal/20 rounded-lg text-energy-teal">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                  </svg>
              </div>
              <span className="text-gray-300 font-medium">Ø Monat</span>
          </div>
          <div className="text-2xl font-bold text-white font-mono">
              {(simulation.netAmount / 12).toFixed(2)}€
          </div>
      </div>

      {/* CTA Button */}
      <button 
        onClick={onSecure}
        className="group w-full py-4 bg-gradient-to-r from-energy-teal to-[#4cd6b3] text-energy-900 font-bold text-lg rounded-xl shadow-[0_0_25px_rgba(100,255,218,0.3)] hover:shadow-[0_0_35px_rgba(100,255,218,0.5)] hover:scale-[1.02] transition-all duration-300 flex items-center justify-center gap-2"
      >
        Jetzt Tarif sichern
        <span className="group-hover:translate-x-1 transition-transform text-xl">→</span>
      </button>
    </div>
  );
};

export default BillPredictor;