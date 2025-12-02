import React from 'react';
import { Shield } from 'lucide-react';

interface PrivacyModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const PrivacyModal: React.FC<PrivacyModalProps> = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
            <div className="bg-energy-800 border border-white/10 p-6 rounded-2xl max-w-sm w-full shadow-2xl animate-scale-up">
                <div className="flex items-center gap-3 mb-4 text-energy-teal">
                    <Shield size={24} />
                    <h3 className="font-bold text-lg text-white">Datenschutz</h3>
                </div>
                <p className="text-gray-300 text-sm leading-relaxed mb-6">
                    Hinweis zum Datenschutz: Im Rahmen der Beratung werden möglicherweise E-Mail-Adressen abgefragt und gespeichert, um Angebote zu versenden. Deine Daten werden vertraulich behandelt.
                </p>
                <button 
                    onClick={onClose}
                    className="w-full py-2.5 bg-energy-teal text-energy-900 font-bold rounded-xl hover:bg-teal-400 transition-colors"
                >
                    Verstanden
                </button>
            </div>
        </div>
    );
};

export default PrivacyModal;
