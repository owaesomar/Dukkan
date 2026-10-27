import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

export interface CartLine {
  productId: number;
  variantId: number;
  productTitle: string;
  variantTitle: string;
  sku: string;
  priceMinor: number;
  currency: string;
  imageUrl: string | null;
  quantity: number;
}

interface CartState {
  storeSlug: string | null;
  items: CartLine[];
  add: (storeSlug: string, line: Omit<CartLine, 'quantity'>) => void;
  setQuantity: (variantId: number, quantity: number) => void;
  remove: (variantId: number) => void;
  clear: () => void;
}

export const useCart = create<CartState>()(
  persist(
    (set) => ({
      storeSlug: null,
      items: [],
      add: (storeSlug, line) =>
        set((state) => {
          const currentItems = state.storeSlug === storeSlug ? state.items : [];
          const existing = currentItems.find((item) => item.variantId === line.variantId);
          if (existing) {
            return {
              storeSlug,
              items: currentItems.map((item) =>
                item.variantId === line.variantId
                  ? { ...item, quantity: Math.min(20, item.quantity + 1) }
                  : item,
              ),
            };
          }
          return { storeSlug, items: [...currentItems, { ...line, quantity: 1 }] };
        }),
      setQuantity: (variantId, quantity) =>
        set((state) => ({
          items:
            quantity <= 0
              ? state.items.filter((item) => item.variantId !== variantId)
              : state.items.map((item) =>
                  item.variantId === variantId
                    ? { ...item, quantity: Math.min(20, quantity) }
                    : item,
                ),
        })),
      remove: (variantId) =>
        set((state) => ({ items: state.items.filter((item) => item.variantId !== variantId) })),
      clear: () => set({ storeSlug: null, items: [] }),
    }),
    {
      name: 'dukkan-storefront-cart',
      storage: createJSONStorage(() => window.localStorage),
    },
  ),
);
