import React from 'react';
import { Zap, Shield } from 'lucide-react';

interface HeaderProps {
    onPrivacyClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onPrivacyClick }) => {
    return (
        <header className="px-6 py-4 bg-slate-900/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-between shrink-0 z-20 shadow-2xl relative overflow-hidden">
            {/* Ambient Background Glow */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent opacity-50"></div>
            
            <div className="flex items-center gap-4 relative z-10">
                {/* Logo with Glow Effect */}
                <div className="relative group">
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-400 to-blue-600 rounded-full blur opacity-30 group-hover:opacity-75 transition duration-500"></div>
                    <div className="relative w-11 h-11 bg-slate-900 rounded-full flex items-center justify-center border border-white/10 shadow-inner">
                        <Zap className="text-cyan-400 fill-cyan-400/20 drop-shadow-[0_0_8px_rgba(34,211,238,0.5)]" size={22} />
                    </div>
                </div>
                
                <div>
                    <h1 className="text-transparent bg-clip-text bg-gradient-to-r from-white via-slate-200 to-slate-400 font-extrabold text-xl tracking-tight leading-none mb-1">
                        Intense Energy
                    </h1>
                    <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1.5 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                            </span>
                            <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider">Sparky Online</span>
                        </div>
                    </div>
                </div>
            </div>

            <button 
                onClick={onPrivacyClick}
                className="group p-2.5 rounded-full bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 transition-all duration-300 hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]"
                title="Datenschutz"
            >
                <Shield size={18} className="text-slate-400 group-hover:text-cyan-300 transition-colors" />
            </button>
        </header>
    );
};

export default Header;
