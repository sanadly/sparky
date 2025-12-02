export enum MessageType {
  TEXT = 'TEXT',
  INPUT_CONSUMPTION = 'INPUT_CONSUMPTION',
  PRODUCT_SELECTION = 'product_selection',
  SIMULATION_RESULT = 'simulation_result',
  INPUT_DATE = 'input_date',
  OFFER_SUCCESS = 'offer_success',
  DURATION_SELECTION = 'duration_selection',
  TARIFF_TYPE_SELECTION = 'tariff_type_selection'
}

export interface Message {
  id: string;
  type: MessageType;
  sender: 'bot' | 'user';
  text?: string;
  data?: any; // For holding widget state
  timestamp: number;
  quickReplies?: string[];
}

export interface Product {
  id: string;
  name: string;
  basePrice: number; // EUR/Year
  workingPrice: number; // Cents/kWh
  totalPrice?: number; // Estimated total for 2500 kWh
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