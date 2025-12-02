import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Zap } from 'lucide-react';
import { Message, MessageType, Product } from '../types';
import ConsumptionVisualizer from './ConsumptionVisualizer';
import ProductCarousel from './ProductCarousel';
import BillPredictor from './BillPredictor';
import DateSelector from './DateSelector';
import DurationSelector from './DurationSelector';
import TariffTypeSelector from './TariffTypeSelector';

interface ChatMessageProps {
    msg: Message;
    userConsumption: number | null;
    onSendMessage: (e?: React.FormEvent, customText?: string) => void;
    onConsumptionConfirm: (consumption: number, householdSize: number, split?: { r1: number, r2: number }) => void;
    onProductSelect: (product: Product) => void;
    onDateSelect: (date: string) => void;
    onSecureOffer: () => void;
    onRestart: () => void;
    onDurationSelect: (duration: string) => void;
    onTariffTypeSelect: (type: string) => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({
    msg,
    userConsumption,
    onSendMessage,
    onConsumptionConfirm,
    onProductSelect,
    onDateSelect,
    onSecureOffer,
    onRestart,
    onDurationSelect,
    onTariffTypeSelect
}) => {
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
                                    onClick={() => onSendMessage(undefined, reply)}
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
                    onConfirm={onConsumptionConfirm}
                    isDoubleTariff={msg.data?.is_dt}
                />
            );
        case MessageType.PRODUCT_SELECTION:
            return <ProductCarousel userConsumption={userConsumption || 2500} onSelectProduct={onProductSelect} products={msg.data?.products} />;
        case MessageType.SIMULATION_RESULT:
            return (
                <BillPredictor
                    product={msg.data.product}
                    consumption={msg.data.consumption}
                    onSecure={onSecureOffer}
                />
            );
        case MessageType.INPUT_DATE:
            return <DateSelector onSelect={onDateSelect} />;
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
                        onClick={onRestart}
                        className="w-full py-3 bg-energy-teal text-energy-900 font-bold rounded-xl hover:scale-[1.02] active:scale-[0.98] transition-all"
                    >
                        Neuen Vertrag simulieren
                    </button>
                </div>
            );
        case MessageType.DURATION_SELECTION:
            return <DurationSelector onSelect={onDurationSelect} />;
        case MessageType.TARIFF_TYPE_SELECTION:
            return <TariffTypeSelector onSelect={onTariffTypeSelect} />;
        default:
            return null;
    }
};

export default ChatMessage;
