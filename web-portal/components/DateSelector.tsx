import React, { useState } from 'react';
import { Calendar, ArrowRight } from 'lucide-react';

interface DateSelectorProps {
  onSelect: (date: string) => void;
}

const DateSelector: React.FC<DateSelectorProps> = ({ onSelect }) => {
  const [customDate, setCustomDate] = useState('');

  const formatDate = (date: Date): string => {
    const d = date.getDate().toString().padStart(2, '0');
    const m = (date.getMonth() + 1).toString().padStart(2, '0');
    const y = date.getFullYear();
    return `${d}.${m}.${y}`;
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (customDate) {
      onSelect(customDate);
    }
  };

  const getNextMonthFirst = () => {
    const d = new Date();
    d.setMonth(d.getMonth() + 1);
    d.setDate(1);
    return d;
  };

  const getInThreeMonthsFirst = () => {
    const d = new Date();
    d.setMonth(d.getMonth() + 3);
    d.setDate(1);
    return d;
  };

  const getInOneYearFirst = () => {
    const d = new Date();
    d.setFullYear(d.getFullYear() + 1);
    d.setDate(1);
    return d;
  };

  const nextMonth = getNextMonthFirst();
  const inThreeMonths = getInThreeMonthsFirst();
  const inOneYear = getInOneYearFirst();

  return (
    <div className="w-full max-w-sm bg-white/10 backdrop-blur-md rounded-2xl p-5 border border-white/10 shadow-xl animate-slide-up">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-energy-teal/20 flex items-center justify-center">
          <Calendar className="text-energy-teal" size={20} />
        </div>
        <div>
          <h3 className="text-white font-medium">Vertragsbeginn wählen</h3>
          <p className="text-xs text-gray-400">Wann soll es losgehen?</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <button
          onClick={() => onSelect(formatDate(nextMonth))}
          className="p-3 rounded-xl bg-white/5 hover:bg-energy-teal/10 border border-white/10 hover:border-energy-teal/50 transition-all text-sm text-white text-left group"
        >
          <span className="block text-xs text-gray-400 mb-0.5">Nächster Monat</span>
          <span className="font-medium group-hover:text-energy-teal">{formatDate(nextMonth)}</span>
        </button>
        <button
          onClick={() => onSelect(formatDate(inThreeMonths))}
          className="p-3 rounded-xl bg-white/5 hover:bg-energy-teal/10 border border-white/10 hover:border-energy-teal/50 transition-all text-sm text-white text-left group"
        >
          <span className="block text-xs text-gray-400 mb-0.5">In 3 Monaten</span>
          <span className="font-medium group-hover:text-energy-teal">{formatDate(inThreeMonths)}</span>
        </button>
         <button
          onClick={() => onSelect(formatDate(inOneYear))}
          className="p-3 rounded-xl bg-white/5 hover:bg-energy-teal/10 border border-white/10 hover:border-energy-teal/50 transition-all text-sm text-white text-left group col-span-2"
        >
          <span className="block text-xs text-gray-400 mb-0.5">In 1 Jahr</span>
          <span className="font-medium group-hover:text-energy-teal">{formatDate(inOneYear)}</span>
        </button>
      </div>

      <form onSubmit={handleCustomSubmit} className="relative">
        <input
          type="text"
          placeholder="Anderes Datum (TT.MM.JJJJ)"
          value={customDate}
          onChange={(e) => setCustomDate(e.target.value)}
          className="w-full bg-white/5 border border-white/10 rounded-xl py-3 px-4 text-white placeholder-gray-500 focus:outline-none focus:border-energy-teal/50 transition-all text-sm"
        />
        <button
          type="submit"
          disabled={!customDate}
          className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-energy-teal text-energy-900 rounded-lg hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 transition-all"
        >
          <ArrowRight size={16} />
        </button>
      </form>
    </div>
  );
};

export default DateSelector;
