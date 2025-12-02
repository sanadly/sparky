import { useState, useRef, useEffect } from 'react';
import { Message, MessageType, Product, UserState } from '../types';
import { generateChatResponse } from '../services/geminiService';

export const useChat = () => {
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

    return {
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
    };
};
