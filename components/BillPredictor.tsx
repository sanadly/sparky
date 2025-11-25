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
    <div className="w-full max-w-sm mx-auto bg-gradient-to-b from-energy-800 to-energy-900 rounded-3xl p-6 shadow-2xl border border-white/10 animate-slide-up">
      <h3 className="text-center text-energy-teal font-bold tracking-wide mb-2">Preis-Vorschau</h3>
      <p className="text-center text-gray-400 text-xs mb-6">{product.name}</p>

      {/* Main Counter */}
      <div className="flex flex-col items-center justify-center mb-6 relative py-4 border-b border-white/5">
        <div className="absolute inset-0 bg-energy-teal/5 blur-3xl rounded-full" />
        <div className="text-5xl font-bold text-white z-10 font-mono tracking-tighter tabular-nums">
          {count.toFixed(2)}
          <span className="text-xl text-energy-teal ml-1">€</span>
        </div>
        <div className="text-xs text-gray-400 mt-2 z-10 bg-black/20 px-3 py-1 rounded-full border border-white/5">
            voraussichtl. pro Jahr
        </div>
      </div>

      {/* Calculation Breakdown (Transparency) */}
      <div className="space-y-3 mb-6 text-sm bg-black/20 p-4 rounded-xl border border-white/5">
          <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                 <div className="w-2 h-2 rounded-full bg-[#233554]" />
                 <span className="text-gray-400">Grundpreis</span>
              </div>
              <span className="font-mono text-white">{simulation.breakdown.baseCost.toFixed(2)} €</span>
          </div>
          <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                 <div className="w-2 h-2 rounded-full bg-[#64ffda]" />
                 <span className="text-gray-400">Verbrauch <span className="text-energy-teal">({consumption} kWh)</span></span>
              </div>
              <span className="font-mono text-white">{simulation.breakdown.usageCost.toFixed(2)} €</span>
          </div>
          <div className="text-[10px] text-gray-500 text-right pt-2 border-t border-white/5">
              Basis: {product.workingPrice} ct/kWh Arbeitspreis
          </div>
      </div>

      {/* Mini Chart */}
      <div className="h-24 w-full mb-6 relative opacity-80">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="100%"
                startAngle={180}
                endAngle={0}
                innerRadius={60}
                outerRadius={80}
                paddingAngle={2}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          {/* Monthly Cost overlay */}
          <div className="absolute bottom-0 left-0 w-full text-center">
             <span className="text-gray-400 text-xs">Ø Monat: </span>
             <span className="text-white font-bold font-mono">{(simulation.netAmount / 12).toFixed(2)}€</span>
          </div>
      </div>

      {/* CTA Button */}
      <button 
        onClick={onSecure}
        className="group w-full py-4 bg-energy-teal text-energy-900 font-bold text-lg rounded-xl shadow-[0_0_20px_rgba(100,255,218,0.4)] animate-pulse-glow hover:scale-105 transition-transform flex items-center justify-center gap-2"
      >
        Jetzt Tarif sichern
        <span className="group-hover:translate-x-1 transition-transform">→</span>
      </button>
    </div>
  );
};

export default BillPredictor;