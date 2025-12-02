import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Zap, Loader2 } from 'lucide-react';
import { Message, MessageType, Product, UserState } from './types';
import { generateChatResponse } from './services/geminiService';
import ConsumptionVisualizer from './components/ConsumptionVisualizer';
import ProductCarousel from './components/ProductCarousel';
import BillPredictor from './components/BillPredictor';
import DateSelector from './components/DateSelector';
import './index.css';

const App = () => {
    const [messages, setMessages] = useState<Message[]>([]);

    const [userState, setUserState] = useState<UserState>({
        householdSize: null,
        consumption: null,
        selectedProductId: null,
        simulation: null
    });

    const [inputValue, setInputValue] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [isAppLoading, setIsAppLoading] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const hasInitialized = useRef(false);

    const addMessage = (msg: Omit<Message, 'id' | 'timestamp'>) => {
        const newMessage: Message = { ...msg, id: Date.now().toString(), timestamp: Date.now() };
        setMessages((prev) => [...prev, newMessage]);
    };

    const processBackendResponse = (response: any) => {
        // 1. Add the text reply
        if (response.reply) {
            addMessage({
                type: MessageType.TEXT,
                sender: 'bot',
                text: response.reply,
                quickReplies: response.quick_replies
            });
        }

        // 2. Handle UI Data / Widgets
        if (response.ui_data) {
            const ui = response.ui_data;

            if (ui.type === 'consumption_input') {
                setTimeout(() => {
                    addMessage({
                        type: MessageType.INPUT_CONSUMPTION,
                        sender: 'bot',
                        data: { is_dt: ui.is_dt }
                    });
                }, 500);
            } else if (ui.type === 'product_selection') {
                // Store products in state if needed, or just pass to widget
                setTimeout(() => {
                    addMessage({
                        type: MessageType.PRODUCT_SELECTION,
                        sender: 'bot',
                        data: { products: ui.products }
                    });
                }, 500);
            } else if (ui.type === 'simulation_result') {
                setTimeout(() => {
                    addMessage({
                        type: MessageType.SIMULATION_RESULT,
                        sender: 'bot',
                        data: ui.data
                    });
                }, 500);
            } else if (ui.type === 'date_input') {
                setTimeout(() => {
                    addMessage({
                        type: MessageType.INPUT_DATE,
                        sender: 'bot',
                        data: {}
                    });
                }, 500);
            } else if (ui.type === 'offer_success') {
                setTimeout(() => {
                    addMessage({
                        type: MessageType.OFFER_SUCCESS,
                        sender: 'bot',
                        data: ui
                    });
                }, 500);
            }
        }
    };

    // Initial Start
    useEffect(() => {
        const initChat = async () => {
            if (hasInitialized.current) return;
            hasInitialized.current = true;

            try {
                // Send a hidden "start" message to trigger the backend welcome flow
                const response = await generateChatResponse([], userState, "start");
                processBackendResponse(response);
            } catch (e) {
                console.error("Failed to start chat", e);
            } finally {
                setIsAppLoading(false);
            }
        };

        initChat();
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, isTyping]);

    const handleConsumptionConfirm = async (consumption: number, householdSize: number, split?: { r1: number, r2: number }) => {
        setUserState({ ...userState, householdSize, consumption });

        let text = `${consumption} kWh`;
        if (split) {
            text = `${split.r1} HT ${split.r2} NT`;
        }

        addMessage({
            type: MessageType.TEXT,
            sender: 'user',
            text: text
        });

        setIsTyping(true);
        try {
            // Send the consumption to the backend
            const response = await generateChatResponse(messages, { ...userState, consumption }, `Mein Verbrauch ist ${text}`);
            processBackendResponse(response);
        } catch (error) {
            console.error(error);
        } finally {
            setIsTyping(false);
        }
    };

    const handleProductSelect = async (product: Product) => {
        setUserState(prev => ({ ...prev, selectedProductId: product.id }));

        addMessage({
            type: MessageType.TEXT,
            sender: 'user',
            text: `Ich wähle ${product.name}`
        });

        setIsTyping(true);
        try {
            const response = await generateChatResponse(messages, userState, `SELECT_PRODUCT:${product.id}`);
            processBackendResponse(response);
        } catch (error) {
            console.error(error);
        } finally {
            setIsTyping(false);
        }
    };

    const handleDateSelect = async (date: string) => {
        addMessage({
            type: MessageType.TEXT,
            sender: 'user',
            text: date
        });

        setIsTyping(true);
        try {
            const response = await generateChatResponse(messages, userState, date);
            processBackendResponse(response);
        } catch (error) {
            console.error(error);
        } finally {
            setIsTyping(false);
        }
    };

    const handleSecureOffer = async () => {
        addMessage({
            type: MessageType.TEXT,
            sender: 'user',
            text: "Angebot sichern"
        });

        setIsTyping(true);
        try {
            const response = await generateChatResponse(messages, userState, "Angebot sichern");
            processBackendResponse(response);
        } catch (error) {
            console.error(error);
        } finally {
            setIsTyping(false);
        }
    };

    const handleRestart = async () => {
        setMessages([]);
        setUserState({
            householdSize: null,
            consumption: null,
            selectedProductId: null,
            simulation: null
        });

        setIsAppLoading(true);
        try {
            // Send a hidden "start" message to trigger the backend welcome flow
            const response = await generateChatResponse([], {
                householdSize: null,
                consumption: null,
                selectedProductId: null,
                simulation: null
            }, "start");
            processBackendResponse(response);
        } catch (e) {
            console.error("Failed to restart chat", e);
        } finally {
            setIsAppLoading(false);
        }
    };

    const handleSendMessage = async (e?: React.FormEvent, customText?: string) => {
        if (e) e.preventDefault();
        const text = customText || inputValue;
        if (!text.trim()) return;

        if (!customText) setInputValue("");

        addMessage({
            type: MessageType.TEXT,
            sender: 'user',
            text: text
        });

        setIsTyping(true);

        try {
            const response = await generateChatResponse(messages, userState, text);
            processBackendResponse(response);
        } catch (error) {
            console.error(error);
        } finally {
            setIsTyping(false);
        }
    };

    const renderMessageContent = (msg: Message) => {
        switch (msg.type) {
            case MessageType.TEXT:
                return (
                    <div className="flex flex-col items-start gap-2 max-w-[85%]">
                        <div className={`p-4 rounded-2xl animate-slide-up shadow-sm ${msg.sender === 'user'
                            ? 'bg-energy-teal text-energy-900 ml-auto rounded-tr-sm'
                            : 'bg-white/10 text-white mr-auto rounded-tl-sm backdrop-blur-md border border-white/5'
                            }`}>
                            <div className="markdown-content">
                                <ReactMarkdown>{msg.text || ''}</ReactMarkdown>
                            </div>
                        </div>
                        {msg.quickReplies && msg.quickReplies.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-1 animate-slide-up">
                                {msg.quickReplies.map((reply, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleSendMessage(undefined, reply)}
                                        className="px-3 py-1.5 bg-white/5 hover:bg-energy-teal/20 border border-white/10 hover:border-energy-teal/50 rounded-full text-xs text-energy-teal transition-all"
                                    >
                                        {reply}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                );
            case MessageType.INPUT_CONSUMPTION:
                return (
                    <ConsumptionVisualizer
                        onConfirm={handleConsumptionConfirm}
                        isDoubleTariff={msg.data?.is_dt}
                    />
                );
            case MessageType.PRODUCT_SELECTION:
                return <ProductCarousel userConsumption={userState.consumption || 2500} onSelectProduct={handleProductSelect} products={msg.data?.products} />;
            case MessageType.SIMULATION_RESULT:
                return (
                    <BillPredictor
                        product={msg.data.product}
                        consumption={msg.data.consumption}
                        onSecure={handleSecureOffer}
                    />
                );
            case MessageType.INPUT_DATE:
                return <DateSelector onSelect={handleDateSelect} />;
            case MessageType.OFFER_SUCCESS:
                return (
                    <div className="bg-white/10 p-6 rounded-2xl border border-white/10 backdrop-blur-md animate-slide-up">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-12 h-12 bg-green-500/20 rounded-full flex items-center justify-center">
                                <Zap className="text-green-400" size={24} />
                            </div>
                            <div>
                                <h3 className="text-white font-bold text-lg">Angebot erstellt!</h3>
                                <p className="text-gray-400 text-sm">Vielen Dank für dein Vertrauen.</p>
                            </div>
                        </div>
                        <div className="bg-white/5 rounded-xl p-4 mb-4">
                            <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">Angebotsnummer</div>
                            <div className="text-2xl font-mono text-energy-teal">{msg.data.offer_id}</div>
                        </div>
                        <button
                            onClick={handleRestart}
                            className="w-full py-3 bg-energy-teal text-energy-900 font-bold rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all"
                        >
                            Neuen Vertrag simulieren
                        </button>
                    </div>
                );
            default:
                return null;
        }
    };

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

                {/* Header */}
                <header className="px-4 py-3 bg-energy-900/90 backdrop-blur-md border-b border-white/5 flex items-center gap-3 shrink-0 z-20">
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
                </header>

                {/* Chat Area */}
                <main className="flex-1 overflow-y-auto p-4 space-y-6 hide-scrollbar scroll-smooth">
                    {messages.map((msg) => (
                        <div key={msg.id} className={`w-full flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                            {renderMessageContent(msg)}
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

                {/* Input Area */}
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
            </div>
        </div>
    );
};

export default App;
