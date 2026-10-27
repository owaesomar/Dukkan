import { beforeEach, describe, expect, it } from 'vitest';
import { useCart } from './cart';

const line = {
  productId: 1,
  variantId: 10,
  productTitle: 'Everyday Backpack',
  variantTitle: 'One size',
  sku: 'bag-one',
  priceMinor: 259900,
  currency: 'BDT',
  imageUrl: null,
};

describe('storefront cart', () => {
  beforeEach(() => useCart.setState({ storeSlug: null, items: [] }));

  it('adds a variant once and increments its quantity on repeat', () => {
    useCart.getState().add('demo-shop', line);
    useCart.getState().add('demo-shop', line);

    expect(useCart.getState().items).toMatchObject([{ variantId: 10, quantity: 2 }]);
  });

  it('keeps one store cart active and supports quantity updates and removal', () => {
    useCart.getState().add('first-shop', line);
    useCart.getState().add('second-shop', { ...line, variantId: 20 });
    expect(useCart.getState().storeSlug).toBe('second-shop');
    expect(useCart.getState().items.map((item) => item.variantId)).toEqual([20]);

    useCart.getState().setQuantity(20, 4);
    expect(useCart.getState().items[0].quantity).toBe(4);
    useCart.getState().remove(20);
    expect(useCart.getState().items).toEqual([]);
  });
});
