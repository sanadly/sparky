import { GoogleGenAI } from "@google/genai";
import { Product, Message, UserState } from '../types';
import { MOCK_PRODUCTS } from '../constants';

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
const modelId = 'gemini-2.5-flash';

export const generateProductPitch = async (product: Product, consumption: number): Promise<string> => {
  try {
    const prompt = `
      Agieren Sie als Energieberater. Sprache: Deutsch.
      Produkt: ${product.name}
      Typ: ${product.isGreen ? 'Ökostrom' : 'Standard Mix'}
      Verbrauch: ${consumption} kWh/Jahr.
      
      Schreiben Sie EINEN Satz als "Warum das zu Ihnen passt"-Tag. Er sollte prägnant, überzeugend und persönlich sein.
      Maximal 15 Wörter. Keine Anführungszeichen.
    `;

    const response = await ai.models.generateContent({
      model: modelId,
      contents: prompt,
    });

    return response.text || "Perfekt für Ihr Nutzungsprofil.";
  } catch (error) {
    console.error("Gemini Error:", error);
    return "Eine gute Wahl für Ihr Zuhause.";
  }
};

export const generateChatResponse = async (history: Message[], userState: UserState, currentMessage: string): Promise<string> => {
    try {
        // Find selected product details if available
        const selectedProduct = userState.selectedProductId 
            ? MOCK_PRODUCTS.find(p => p.id === userState.selectedProductId)
            : null;

        const contextPrompt = `
        System: Du bist 'Sparky', der KI-Berater für Intense Energy. 
        Deine Persönlichkeit: Hilfreich, freundlich, professionell, aber locker.
        Sprache: Deutsch.
        
        Aktueller Nutzer-Kontext:
        - Jahresverbrauch: ${userState.consumption > 0 ? userState.consumption + ' kWh' : 'Noch nicht angegeben'}
        - Haushaltsgröße: ${userState.householdSize > 0 ? userState.householdSize + ' Personen' : 'Unbekannt'}
        - Gewähltes Produkt: ${selectedProduct ? selectedProduct.name : 'Noch keines ausgewählt'}
        ${selectedProduct ? `- Produktdetails: ${selectedProduct.description}, ${selectedProduct.isGreen ? 'Ökostrom' : 'Standard'}, Preisgarantie: ${selectedProduct.contractDuration} Monate.` : ''}
        
        Aufgabe: Antworte auf die Nachricht des Nutzers. Wenn er Fragen zum gewählten Tarif hat, nutze die Produktdetails. Fasse dich kurz (max 2-3 Sätze), außer es ist eine komplexe Erklärung nötig.
        `;

        // Simplify history for token efficiency
        const chatHistory = history.map(m => `${m.sender === 'user' ? 'Nutzer' : 'Bot'}: ${m.text || '[Interaktives Element]'}`).join('\n');

        const response = await ai.models.generateContent({
            model: modelId,
            contents: `
            ${contextPrompt}
            
            Verlauf:
            ${chatHistory}
            
            Nutzer: ${currentMessage}
            Bot:
            `
        });
        return response.text || "Ich verarbeite diese Information...";
    } catch (error) {
        console.error("Chat Error", error);
        return "Entschuldigung, ich habe gerade Verbindungsprobleme. Können Sie das wiederholen?";
    }
}