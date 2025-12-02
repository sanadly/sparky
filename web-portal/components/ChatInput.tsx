import React from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
    inputValue: string;
    setInputValue: (value: string) => void;
    handleSendMessage: (e?: React.FormEvent) => void;
    isTyping: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ inputValue, setInputValue, handleSendMessage, isTyping }) => {
    return (
        <div className="p-4 bg-energy-900/80 backdrop-blur-md border-t border-white/5 shrink-0 z-20">
            <form
                onSubmit={(e) => handleSendMessage(e)}
                className="flex items-center gap-2 bg-white/5 p-1.5 pl-4 rounded-full border border-white/10 focus-within:border-energy-teal/50 focus-within:bg-white/10 transition-all"
            >
                <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Schreiben Sie eine Nachricht..."
                    className="flex-1 bg-transparent border-none outline-none text-white placeholder-gray-500 text-sm py-2"
                    disabled={isTyping}
                />
                <button
                    type="submit"
                    disabled={!inputValue.trim() || isTyping}
                    className={`p-2.5 rounded-full transition-all ${!inputValue.trim() || isTyping
                        ? 'bg-white/5 text-gray-500 cursor-not-allowed'
                        : 'bg-energy-teal text-energy-900 hover:scale-105 active:scale-95 shadow-[0_0_10px_rgba(100,255,218,0.3)]'
                        }`}
                >
                    {isTyping ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                </button>
            </form>
        </div>
    );
};

export default ChatInput;
