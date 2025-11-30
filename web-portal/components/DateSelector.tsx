import React, { useState } from 'react';
import { Calendar, ArrowRight } from 'lucide-react';

interface Props {
  onDateSubmit: (date: string) => void;
}

const DateSelector: React.FC<Props> = ({ onDateSubmit }) => {
  const [date, setDate] = useState('');
  
  React.useEffect(() => {
      console.log("DateSelector mounted");
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (date) {
      // Convert YYYY-MM-DD to DD.MM.YYYY for chat display
      const [y, m, d] = date.split('-');
      onDateSubmit(`${d}.${m}.${y}`);
    }
  };

  const getFutureDate = (monthsAhead: number) => {
    const d = new Date();
    d.setMonth(d.getMonth() + monthsAhead);
    d.setDate(1); // 1st of the month
    return d.toISOString().split('T')[0];
  };

  const quickDates = [
    { label: 'Nächster Monat', value: getFutureDate(1) },
    { label: 'In 3 Monaten', value: getFutureDate(3) },
    { label: 'Nächstes Jahr', value: getFutureDate(12) },
  ];

  return (
    <div className="w-full max-w-md mx-auto mt-4 animate-slide-up relative z-30">
      <div className="bg-energy-800/90 backdrop-blur-xl rounded-2xl p-6 border border-energy-teal/30 shadow-[0_0_30px_rgba(0,0,0,0.3)]">
        <div className="flex items-center gap-3 mb-4 text-energy-teal">
          <Calendar className="w-6 h-6" />
          <h3 className="text-lg font-bold text-white">Startdatum wählen</h3>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
              className="w-full bg-black/20 border border-white/20 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-energy-teal focus:ring-1 focus:ring-energy-teal transition-all"
              required
            />
          </div>

          <div className="flex flex-wrap gap-2">
            {quickDates.map((qd) => (
              <button
                key={qd.label}
                type="button"
                onClick={() => setDate(qd.value)}
                className="text-xs px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 text-gray-300 border border-white/10 transition-colors"
              >
                {qd.label}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={!date}
            className="w-full bg-gradient-to-r from-energy-teal to-blue-500 text-white font-bold py-3 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            Bestätigen <ArrowRight size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default DateSelector;
