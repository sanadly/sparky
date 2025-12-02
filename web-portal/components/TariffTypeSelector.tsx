import React from 'react';
import { Zap, Sun, Layers } from 'lucide-react';

interface TariffTypeSelectorProps {
    onSelect: (type: string) => void;
}

const TariffTypeSelector: React.FC<TariffTypeSelectorProps> = ({ onSelect }) => {
    const options = [
        { label: 'Einzeltarif', value: 'Einzeltarif', icon: Zap, desc: 'Standard für die meisten Haushalte' },
        { label: 'Doppeltarif', value: 'Doppeltarif', icon: Sun, desc: 'HT/NT für Nachtspeicher/Wärmepumpen' },
        { label: 'Egal', value: 'Egal', icon: Layers, desc: 'Alle Optionen anzeigen' }
    ];

    return (
        <div className="flex flex-col gap-3 w-full max-w-sm animate-slide-up">
            <div className="text-white/80 text-sm mb-1 ml-1">Wähle deinen Tarif-Typ:</div>
            <div className="grid grid-cols-1 gap-2">
                {options.map((opt) => (
                    <button
                        key={opt.label}
                        onClick={() => onSelect(opt.value)}
                        className="flex items-center gap-4 p-4 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-energy-teal/50 rounded-xl transition-all group text-left"
                    >
                        <div className="w-10 h-10 rounded-full bg-energy-teal/10 flex items-center justify-center group-hover:bg-energy-teal/20 transition-colors">
                            <opt.icon className="text-energy-teal" size={20} />
                        </div>
                        <div>
                            <div className="text-white font-medium">{opt.label}</div>
                            <div className="text-xs text-gray-400">{opt.desc}</div>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default TariffTypeSelector;
