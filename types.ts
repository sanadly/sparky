export enum MessageType {
  TEXT = 'TEXT',
  INPUT_CONSUMPTION = 'INPUT_CONSUMPTION',
  PRODUCT_SELECTION = 'PRODUCT_SELECTION',
  SIMULATION_RESULT = 'SIMULATION_RESULT',
}

export interface Message {
  id: string;
  type: MessageType;
  sender: 'bot' | 'user';
  text?: string;
  data?: any; // For holding widget state
  timestamp: number;
}

export interface Product {
  id: string;
  name: string;
  basePrice: number; // EUR/Year
  workingPrice: number; // Cents/kWh
  isGreen: boolean;
  contractDuration: number; // Months
  description: string;
}

export interface SimulationResult {
  netAmount: number;
  currency: string;
  breakdown: {
    baseCost: number;
    usageCost: number;
  };
}

export interface UserState {
  consumption: number; // kWh
  householdSize: number;
  selectedProductId: string | null;
  simulation: SimulationResult | null;
}