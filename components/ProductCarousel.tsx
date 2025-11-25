import React from 'react';
import { Product } from '../types';
import { MOCK_PRODUCTS } from '../constants';
import ProductCard from './ProductCard';

interface Props {
  userConsumption: number;
  onSelectProduct: (product: Product) => void;
}

const ProductCarousel: React.FC<Props> = ({ userConsumption, onSelectProduct }) => {
  const [selectedId, setSelectedId] = React.useState<string | null>(null);

  const handleSelect = (product: Product) => {
    setSelectedId(product.id);
    onSelectProduct(product);
  };

  return (
    <div className="w-full animate-slide-up">
      <h3 className="text-lg text-energy-teal font-bold mb-3 pl-4">Empfohlene Tarife</h3>
      <div className="flex overflow-x-auto gap-4 px-4 pb-8 pt-4 hide-scrollbar snap-x snap-mandatory">
        {MOCK_PRODUCTS.map(product => (
          <ProductCard 
            key={product.id}
            product={product}
            userConsumption={userConsumption}
            onSelect={handleSelect}
            isSelected={selectedId === product.id}
          />
        ))}
        {/* Spacer for right padding */}
        <div className="min-w-[20px]" />
      </div>
    </div>
  );
};

export default ProductCarousel;