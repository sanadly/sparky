import React, { useState, useEffect, useRef } from 'react';
import { Message, MessageType, Product, UserState } from './types';
import ConsumptionVisualizer from './components/ConsumptionVisualizer';
import ProductCarousel from './components/ProductCarousel';
import BillPredictor from './components/BillPredictor';
import { Zap, Send, Loader2 } from 'lucide-react';
import { generateChatResponse } from './services/geminiService';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [userState, setUserState] = useState<UserState>({
    consumption: 0,
    householdSize: 0,
    selectedProductId: null,
    simulation: null
  });
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isAppLoading, setIsAppLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const addMessage = (msg: Omit<Message, 'id' | 'timestamp'>) => {
    const newMessage: Message = {
      ...msg,
      id: Math.random().toString(36).substr(2, 9),
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Initial App Load Simulator
  useEffect(() => {
      // Simulate initial connection
      const timer = setTimeout(() => {
          setIsAppLoading(false);
          // Start typing immediately after load
          setIsTyping(true);
          
          // Bot welcome sequence
          setTimeout(() => {
            addMessage({
                type: MessageType.TEXT,
                sender: 'bot',
                text: "Hallo! Ich bin Sparky, Ihr intelligenter Energieberater. Lassen Sie uns den perfekten Ökostrom-Tarif für Ihr Zuhause finden."
            });
            
            // Second message sequence
            setTimeout(() => {
                addMessage({
                    type: MessageType.TEXT,
                    sender: 'bot',
                    text: "Um zu beginnen, muss ich Ihren jährlichen Energieverbrauch verstehen. Nutzen Sie dazu den Visualisierer unten."
                });
                
                // Widget sequence
                setTimeout(() => {
                    addMessage({
                        type: MessageType.INPUT_CONSUMPTION,
                        sender: 'bot',
                    });
                    setIsTyping(false);
                }, 600);
                
            }, 1200);

          }, 1000);
      }, 1500);

      return () => clearTimeout(timer);
  }, []);

  // Handlers for interactive widgets
  const handleConsumptionConfirm = (consumption: number, householdSize: number) => {
    setUserState(prev => ({ ...prev, consumption, householdSize }));
    
    // Add user feedback message
    addMessage({
        type: MessageType.TEXT,
        sender: 'user',
        text: `Ich verbrauche etwa ${consumption} kWh/Jahr.`
    });

    setIsTyping(true);
    setTimeout(() => {
        addMessage({
            type: MessageType.TEXT,
            sender: 'bot',
            text: `Verstanden! Basierend auf einem ${householdSize}-Personen-Haushalt mit ${consumption} kWh Verbrauch habe ich diese passenden Pläne gefunden:`
        });
        setTimeout(() => {
            addMessage({
                type: MessageType.PRODUCT_SELECTION,
                sender: 'bot',
            });
            setIsTyping(false);
        }, 500);
    }, 1200);
  };

  const handleProductSelect = (product: Product) => {
    setUserState(prev => ({ ...prev, selectedProductId: product.id }));
    
    setIsTyping(true);
    setTimeout(() => {
        addMessage({
            type: MessageType.SIMULATION_RESULT,
            sender: 'bot',
            data: { product, consumption: userState.consumption }
        });
        setIsTyping(false);
    }, 800);
  };

  const handleSecureOffer = () => {
      addMessage({
          type: MessageType.TEXT,
          sender: 'user',
          text: "Ich möchte diesen Preis sichern."
      });
      setIsTyping(true);
      setTimeout(() => {
          addMessage({
              type: MessageType.TEXT,
              sender: 'bot',
              text: "Gute Wahl! Ich erstelle jetzt Ihr offizielles Angebot. Sie können mir jetzt gerne noch Fragen zu Ihrem Vertrag stellen."
          });
          setIsTyping(false);
      }, 2000);
  };

  const handleSendMessage = async (e?: React.FormEvent) => {
      if (e) e.preventDefault();
      if (!inputValue.trim()) return;

      const text = inputValue;
      setInputValue("");
      
      addMessage({
          type: MessageType.TEXT,
          sender: 'user',
          text: text
      });

      setIsTyping(true);

      try {
        const response = await generateChatResponse(messages, userState, text);
        addMessage({
            type: MessageType.TEXT,
            sender: 'bot',
            text: response
        });
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
          <div className={`p-4 rounded-2xl max-w-[85%] animate-slide-up shadow-sm ${
            msg.sender === 'user' 
              ? 'bg-energy-teal text-energy-900 ml-auto rounded-tr-sm' 
              : 'bg-white/10 text-white mr-auto rounded-tl-sm backdrop-blur-md border border-white/5'
          }`}>
            {msg.text}
          </div>
        );
      case MessageType.INPUT_CONSUMPTION:
        return <ConsumptionVisualizer onConfirm={handleConsumptionConfirm} />;
      case MessageType.PRODUCT_SELECTION:
        return <ProductCarousel userConsumption={userState.consumption} onSelectProduct={handleProductSelect} />;
      case MessageType.SIMULATION_RESULT:
        return (
            <BillPredictor 
                product={msg.data.product} 
                consumption={msg.data.consumption} 
                onSecure={handleSecureOffer} 
            />
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
                    onSubmit={handleSendMessage}
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
                        className={`p-2.5 rounded-full transition-all ${
                            !inputValue.trim() || isTyping 
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