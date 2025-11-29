import { Message, UserState } from '../types';

// Generate a random session ID if one doesn't exist
const getSessionId = () => {
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
    localStorage.setItem('session_id', sessionId);
  }
  return sessionId;
};

export const generateChatResponse = async (history: Message[], userState: UserState, currentMessage: string): Promise<string> => {
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: getSessionId(),
                message: currentMessage,
                channel: 'web'
            }),
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        return data.reply || "Entschuldigung, ich habe keine Antwort erhalten.";
    } catch (error) {
        console.error("Chat Error", error);
        return "Entschuldigung, ich kann den Server gerade nicht erreichen. Bitte versuchen Sie es später noch einmal.";
    }
}

// The backend now handles product pitches via the chat flow usually, 
// but if the UI calls this directly, we might need a specific endpoint or logic.
export const generateProductPitch = async (product: any, consumption: number): Promise<string> => {
    try {
        const response = await fetch('/api/pitch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_name: product.name,
                is_green: product.isGreen,
                consumption: consumption
            }),
        });

        if (!response.ok) return "Eine gute Wahl für Ihr Zuhause.";

        const data = await response.json();
        return data.pitch || "Perfekt für Ihr Nutzungsprofil.";
    } catch (error) {
        console.error("Pitch Error", error);
        return "Eine gute Wahl für Ihr Zuhause.";
    }
};