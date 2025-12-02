import React, { useState, useRef, useEffect } from 'react';
import { Zap, Loader2 } from 'lucide-react';
import { useChat } from './hooks/useChat';
import Header from './components/Header';
import ChatInput from './components/ChatInput';
import PrivacyModal from './components/PrivacyModal';
import ChatMessage from './components/ChatMessage';
import './index.css';

const App = () => {
    const {
        messages,
        userState,
        inputValue,
        setInputValue,
        isTyping,
        isAppLoading,
        handleConsumptionConfirm,
        handleProductSelect,
        handleDateSelect,
        handleSecureOffer,
        handleRestart,
        handleDurationSelect,
        handleTariffTypeSelect,
        handleSendMessage
    } = useChat();

    const [showPrivacy, setShowPrivacy] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    if (isAppLoading) {
        return (
            <div className="min-h-screen bg-energy-900 flex flex-col items-center justify-center relative overflow-hidden">
                <div className="absolute w-96 h-96 bg-energy-teal/20 rounded-full blur-[100px] animate-pulse" />
                <Zap className="text-energy-teal w-16 h-16 animate-bounce relative z-10 mb-4" />
                <div className="text-white font-mono relative z-10 flex items-center gap-2">
                    <Loader2 className="animate-spin" size={16} />
                    Verbinde mit Intense Energy...
                </div>
            </div>
        )
    }

    return (
        <div className="fixed inset-0 bg-energy-900 flex flex-col items-center justify-center font-sans overflow-hidden">

            {/* Background Ambient Effects */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
                <div className="absolute -top-20 -right-20 w-96 h-96 bg-energy-teal/10 rounded-full blur-[100px] animate-pulse" />
                <div className="absolute top-1/2 -left-20 w-72 h-72 bg-blue-600/10 rounded-full blur-[80px]" />
            </div>

            {/* Main Interface Container */}
            <div className="w-full h-full md:h-[95vh] md:max-w-md bg-energy-800/80 md:rounded-3xl shadow-2xl flex flex-col relative z-10 border border-white/5 backdrop-blur-sm overflow-hidden">

                <Header onPrivacyClick={() => setShowPrivacy(true)} />

                <PrivacyModal isOpen={showPrivacy} onClose={() => setShowPrivacy(false)} />

                {/* Chat Area */}
                <main className="flex-1 overflow-y-auto p-4 space-y-6 hide-scrollbar scroll-smooth">
                    {messages.map((msg) => (
                        <div key={msg.id} className={`w-full flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            <ChatMessage 
                                msg={msg}
                                userConsumption={userState.consumption}
                                onSendMessage={handleSendMessage}
                                onConsumptionConfirm={handleConsumptionConfirm}
                                onProductSelect={handleProductSelect}
                                onDateSelect={handleDateSelect}
                                onSecureOffer={handleSecureOffer}
                                onRestart={handleRestart}
                                onDurationSelect={handleDurationSelect}
                                onTariffTypeSelect={handleTariffTypeSelect}
                            />
                        </div>
                    ))}
                    {isTyping && (
                        <div className="flex gap-2 p-4 bg-white/5 rounded-2xl w-24 items-center animate-slide-up rounded-tl-sm backdrop-blur-md border border-white/5">
                            <div className="w-2 h-2 bg-energy-teal rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                            <div className="w-2 h-2 bg-energy-teal rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                            <div className="w-2 h-2 bg-energy-teal rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                        </div>
                    )}
                    <div ref={messagesEndRef} className="h-2" />
                </main>

                <ChatInput 
                    inputValue={inputValue}
                    setInputValue={setInputValue}
                    handleSendMessage={handleSendMessage}
                    isTyping={isTyping}
                />
            </div>
        </div>
    );
};

export default App;
