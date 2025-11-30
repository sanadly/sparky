import React, { useState, useEffect } from 'react';
import { INITIAL_CONSUMPTION } from '../constants';
import { Home, User, Users, Tv, WashingMachine, Zap, Car } from 'lucide-react';

interface Props {
  onConfirm: (consumption: number, householdSize: number) => void;
}

const ConsumptionVisualizer: React.FC<Props> = ({ onConfirm }) => {
  const [consumption, setConsumption] = useState(INITIAL_CONSUMPTION);
  const [householdSize, setHouseholdSize] = useState(2);
  const [intensity, setIntensity] = useState(0.5);

  useEffect(() => {
    // Map consumption 1000-6000 to opacity/intensity 0-1
    const val = Math.min(Math.max((consumption - 1000) / 5000, 0), 1);
    setIntensity(val);
  }, [consumption]);

  const handlePreset = (size: number, kwh: number) => {
    setHouseholdSize(size);
    setConsumption(kwh);
  };

  // Appliance indicators based on consumption
  const appliances = [
    { icon: Tv, label: 'Basis', threshold: 0 },
    { icon: WashingMachine, label: 'Komfort', threshold: 2000 },
    { icon: Zap, label: 'Klima/Trockner', threshold: 3500 },
    { icon: Car, label: 'E-Auto', threshold: 5000 },
  ];

  return (
    <div className="w-full max-w-sm mx-auto bg-white/5 backdrop-blur-lg border border-white/10 rounded-2xl p-6 shadow-2xl animate-slide-up select-none">
      <h3 className="text-xl font-bold text-energy-teal mb-4 text-center">Zuhause-Visualisierer</h3>
      
      {/* Interactive House Graphic */}
      <div className="relative h-48 w-full mb-6 flex justify-center items-center bg-gradient-to-b from-transparent to-black/20 rounded-xl overflow-hidden border border-white/5">
        
        {/* Dynamic Background Glow */}
        <div 
            className="absolute bottom-0 w-full h-full bg-energy-teal transition-opacity duration-700 blur-[60px]"
            style={{ opacity: intensity * 0.4 }}
        />
        
        {/* House SVG */}
        <svg viewBox="0 0 200 160" className="w-48 h-40 relative z-10 drop-shadow-2xl transition-transform duration-500" style={{ transform: `scale(${1 + intensity * 0.1})` }}>
          {/* Roof */}
          <path d="M20,60 L100,10 L180,60" fill="none" stroke="#64ffda" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M30,60 L100,18 L170,60" fill="#0a192f" opacity="0.8" />
          
          {/* Body */}
          <rect x="35" y="60" width="130" height="90" fill="#112240" stroke="#233554" strokeWidth="3" />
          
          {/* Windows - Left (Bedroom) */}
          <rect x="50" y="75" width="30" height="30" rx="2" fill={intensity > 0.1 ? "#fbbf24" : "#1e293b"} className="transition-colors duration-500" />
          <path d="M50,90 L80,90 M65,75 L65,105" stroke="#112240" strokeWidth="2" />

          {/* Windows - Right (Living Room) */}
          <rect x="120" y="75" width="30" height="30" rx="2" fill={intensity > 0.4 ? "#fbbf24" : "#1e293b"} className="transition-colors duration-500" />
          <path d="M120,90 L150,90 M135,75 L135,105" stroke="#112240" strokeWidth="2" />

          {/* Door */}
          <rect x="90" y="100" width="20" height="50" fill="#0f172a" stroke="#64ffda" strokeWidth="1" />
          
          {/* Garage / Side extension if high consumption */}
          <path d="M165,100 L200,100 L200,150 L165,150 Z" fill="#112240" stroke="#233554" strokeWidth="2" 
                style={{ opacity: intensity > 0.7 ? 1 : 0, transition: 'opacity 0.5s ease' }} />
        </svg>

        {/* Appliance Icons Row */}
        <div className="absolute bottom-2 left-0 w-full flex justify-center gap-4 z-20 px-2">
          {appliances.map((Appliance, idx) => (
            <div 
              key={idx}
              className={`p-1.5 rounded-full transition-all duration-500 border border-white/5 ${consumption >= Appliance.threshold ? 'bg-energy-teal text-energy-900 scale-110 shadow-[0_0_10px_rgba(100,255,218,0.5)]' : 'bg-black/40 text-gray-600 scale-90 grayscale'}`}
              title={Appliance.label}
            >
              <Appliance.icon size={14} />
            </div>
          ))}
        </div>
      </div>

      {/* Household Presets */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        <button 
          onClick={() => handlePreset(1, 1500)}
          className={`py-2 px-3 rounded-lg flex flex-col items-center gap-1 transition-all border ${householdSize === 1 ? 'bg-energy-teal/10 border-energy-teal text-energy-teal' : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'}`}
        >
          <User size={18} />
          <span className="text-[10px] uppercase tracking-wider font-semibold">Single</span>
        </button>
        <button 
          onClick={() => handlePreset(2, 2800)}
          className={`py-2 px-3 rounded-lg flex flex-col items-center gap-1 transition-all border ${householdSize === 2 ? 'bg-energy-teal/10 border-energy-teal text-energy-teal' : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'}`}
        >
          <Users size={18} />
          <span className="text-[10px] uppercase tracking-wider font-semibold">Paar</span>
        </button>
        <button 
          onClick={() => handlePreset(4, 4500)}
          className={`py-2 px-3 rounded-lg flex flex-col items-center gap-1 transition-all border ${householdSize === 4 ? 'bg-energy-teal/10 border-energy-teal text-energy-teal' : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'}`}
        >
          <Home size={18} />
          <span className="text-[10px] uppercase tracking-wider font-semibold">Familie</span>
        </button>
      </div>

      {/* Slider */}
      <div className="mb-8 px-1">
        <div className="flex justify-between items-baseline mb-3">
          <span className="text-gray-400 text-xs">Jahresverbrauch</span>
          <div className="flex items-baseline gap-1">
            <span className="text-3xl font-bold text-white font-mono tracking-tight">{consumption}</span>
            <span className="text-sm text-energy-teal">kWh</span>
          </div>
        </div>
        
        <div className="relative h-8 flex items-center">
            <input 
              type="range" 
              min="1000" 
              max="6000" 
              step="100" 
              value={consumption} 
              onChange={(e) => setConsumption(parseInt(e.target.value))}
              className="absolute w-full h-8 opacity-0 cursor-pointer z-20"
            />
            <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden relative z-10 box-border border border-white/5">
                <div 
                    className="h-full bg-gradient-to-r from-blue-500 via-teal-400 to-energy-teal transition-all duration-150"
                    style={{ width: `${((consumption - 1000) / 5000) * 100}%` }}
                />
            </div>
            {/* Custom Thumb (Visual only) */}
            <div 
                className="absolute h-6 w-6 bg-energy-teal rounded-full shadow-[0_0_15px_rgba(100,255,218,0.6)] border-4 border-energy-800 z-10 pointer-events-none transition-all duration-150 flex items-center justify-center"
                style={{ left: `calc(${((consumption - 1000) / 5000) * 100}% - 12px)` }}
            >
                <div className="w-1.5 h-1.5 bg-energy-900 rounded-full" />
            </div>
        </div>
        <div className="flex justify-between text-[10px] text-gray-500 mt-1 font-mono">
          <span>1000 kWh</span>
          <span>6000 kWh</span>
        </div>
      </div>

      <button 
        onClick={() => onConfirm(consumption, householdSize)}
        className="w-full py-3.5 bg-gradient-to-r from-teal-500 to-blue-600 rounded-xl font-bold text-white shadow-lg hover:shadow-teal-500/30 hover:scale-[1.02] transition-all active:scale-95 flex items-center justify-center gap-2"
      >
        <span>Berechnung starten</span>
        <Zap size={16} className="fill-white" />
      </button>
    </div>
  );
};

export default ConsumptionVisualizer;