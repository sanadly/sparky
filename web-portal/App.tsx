import React, { useState, useRef, useEffect } from 'react';
import { Zap, Loader2 } from 'lucide-react';
import { Message, MessageType, Product, UserState } from './types';
import { generateChatResponse } from './services/geminiService';
import Header from './components/Header';
import ChatInput from './components/ChatInput';
import PrivacyModal from './components/PrivacyModal';
import ChatMessage from './components/ChatMessage';
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
    const [showPrivacy, setShowPrivacy] = useState(false);
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
            } else if (ui.type === 'duration_selection') {
                setTimeout(() => {
                    addMessage({
                        type: MessageType.DURATION_SELECTION,
                        sender: 'bot',
                        data: {}
                    });
                }, 500);
            } else if (ui.type === 'tariff_type_selection') {
                setTimeout(() => {
                    addMessage({
                        type: MessageType.TARIFF_TYPE_SELECTION,
                        sender: 'bot',
                        data: {}
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

    const handleDurationSelect = async (duration: string) => {
        addMessage({
            type: MessageType.TEXT,
            sender: 'user',
            text: duration
        });

        setIsTyping(true);
        try {
            const response = await generateChatResponse(messages, userState, duration);
            processBackendResponse(response);
        } catch (error) {
            console.error(error);
        } finally {
            setIsTyping(false);
        }
    };

    const handleTariffTypeSelect = async (type: string) => {
        addMessage({
            type: MessageType.TEXT,
            sender: 'user',
            text: type
        });

        setIsTyping(true);
        try {
            const response = await generateChatResponse(messages, userState, type);
            processBackendResponse(response);
        } catch (error) {
            console.error(error);
        } finally {
            setIsTyping(false);
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
