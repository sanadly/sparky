import { Product } from './types';

export const MOCK_PRODUCTS: Product[] = [
  {
    id: 'prod_1',
    name: 'Intensive Energy 12',
    basePrice: 120.00,
    workingPrice: 32.5,
    isGreen: false,
    contractDuration: 12,
    description: 'Zuverlässige Grundversorgung für stabile Haushalte.'
  },
  {
    id: 'prod_2',
    name: 'Eco Future Flex',
    basePrice: 145.00,
    workingPrice: 34.0,
    isGreen: true,
    contractDuration: 1,
    description: '100 % Wasserkraft mit monatlicher Kündigungsoption.'
  },
  {
    id: 'prod_3',
    name: 'Smart Family Saver',
    basePrice: 90.00,
    workingPrice: 31.0,
    isGreen: true,
    contractDuration: 24,
    description: 'Beste Preise für 2 Jahre gesichert. Ideal für Familien.'
  }
];

export const INITIAL_CONSUMPTION = 2500;