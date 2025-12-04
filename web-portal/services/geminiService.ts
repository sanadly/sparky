import { Message, UserState } from '../types';
import { apiClient } from './api/client';

// Generate a random session ID if one doesn't exist
const getSessionId = () => {
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    sessionId = Math.random().toString(36).substring(2) + Date.now().toString(36);
    localStorage.setItem('session_id', sessionId);
  }
  return sessionId;
};

export const generateChatResponse = async (history: Message[], userState: UserState, currentMessage: string): Promise<any> => {
    try {
        return await apiClient.chat(getSessionId(), currentMessage);
    } catch (error) {
        console.error("Chat Error", error);
        return { reply: "Entschuldigung, ich kann den Server gerade nicht erreichen. Bitte versuchen Sie es später noch einmal." };
    }
}

// The backend now handles product pitches via the chat flow usually, 
// but if the UI calls this directly, we might need a specific endpoint or logic.
export const generateProductPitch = async (product: any, consumption: number): Promise<string> => {
    try {
        const data = await apiClient.pitch(product.name, product.isGreen, consumption);
        return data.pitch || "Perfekt für Ihr Nutzungsprofil.";
    } catch (error) {
        console.error("Pitch Error", error);
        return "Eine gute Wahl für Ihr Zuhause.";
    }
};