import React from 'react';
import { Zap, Shield } from 'lucide-react';

interface HeaderProps {
    onPrivacyClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onPrivacyClick }) => {
    return (
        <header className="px-4 py-3 bg-energy-900/90 backdrop-blur-md border-b border-white/5 flex items-center justify-between shrink-0 z-20">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-teal-400 to-blue-500 rounded-full flex items-center justify-center shadow-lg">
                    <Zap className="text-white fill-white" size={20} />
                </div>
                <div>
                    <h1 className="text-white font-bold text-lg leading-tight">Intense Energy</h1>
                    <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_5px_rgba(34,197,94,0.6)]"></span>
                        <span className="text-xs text-gray-400 font-medium">Sparky Online</span>
                    </div>
                </div>
            </div>
            <button 
                onClick={onPrivacyClick}
                className="p-2 text-gray-400 hover:text-white hover:bg-white/10 rounded-full transition-colors"
                title="Datenschutz"
            >
                <Shield size={20} />
            </button>
        </header>
    );
};

export default Header;
