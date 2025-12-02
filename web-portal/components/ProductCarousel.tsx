import React, { useRef } from 'react';
import { Product } from '../types';
import { MOCK_PRODUCTS } from '../constants';
import ProductCard from './ProductCard';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface Props {
  userConsumption: number;
  onSelectProduct: (product: Product) => void;
  products?: Product[];
}

const ProductCarousel: React.FC<Props> = ({ userConsumption, onSelectProduct, products }) => {
  const [selectedId, setSelectedId] = React.useState<string | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const displayProducts = products && products.length > 0 ? products : MOCK_PRODUCTS;

  const handleSelect = (product: Product) => {
    setSelectedId(product.id);
    onSelectProduct(product);
  };

  const scroll = (direction: 'left' | 'right') => {
    if (scrollContainerRef.current) {
      const scrollAmount = 300;
      const newScrollLeft = scrollContainerRef.current.scrollLeft + (direction === 'right' ? scrollAmount : -scrollAmount);
      scrollContainerRef.current.scrollTo({
        left: newScrollLeft,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="w-full animate-slide-up relative group">
      <div className="flex items-center justify-between mb-3 px-4">
          <h3 className="text-lg text-energy-teal font-bold">Empfohlene Tarife</h3>
          <div className="flex gap-2">
              <button 
                  onClick={() => scroll('left')}
                  className="p-1.5 rounded-full bg-white/5 hover:bg-energy-teal/20 text-white/50 hover:text-energy-teal transition-all border border-white/5 hover:border-energy-teal/30"
              >
                  <ChevronLeft size={18} />
              </button>
              <button 
                  onClick={() => scroll('right')}
                  className="p-1.5 rounded-full bg-white/5 hover:bg-energy-teal/20 text-white/50 hover:text-energy-teal transition-all border border-white/5 hover:border-energy-teal/30"
              >
                  <ChevronRight size={18} />
              </button>
          </div>
      </div>
      
      <div 
        ref={scrollContainerRef}
        className="flex overflow-x-auto gap-4 px-4 pb-8 pt-4 hide-scrollbar snap-x snap-mandatory scroll-smooth"
      >
        {displayProducts.map(product => (
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