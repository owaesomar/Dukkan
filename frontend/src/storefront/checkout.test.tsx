import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { storeApi } from '../lib/api';
import type { CheckoutResult } from '../lib/api';
import { useCart } from './cart';
import { CheckoutPage } from './pages';

function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname}{location.hash}</output>;
}

const placedOrder: CheckoutResult = {
  order_code: 'DK-TESTORDER',
  status: 'pending',
  payment_method: 'cash_on_delivery',
  payment_status: 'unpaid',
  subtotal_minor: 259900,
  shipping_minor: 0,
  total_minor: 259900,
  currency: 'BDT',
  tracking_token: 'a'.repeat(64),
  items: [],
};

describe('COD checkout page', () => {
  beforeEach(() => {
    useCart.setState({
      storeSlug: 'demo-shop',
      items: [{
        productId: 1,
        variantId: 10,
        productTitle: 'Everyday Backpack',
        variantTitle: 'One size',
        sku: 'BAG-ONE',
        priceMinor: 259900,
        currency: 'BDT',
        imageUrl: null,
        quantity: 1,
      }],
    });
  });

  it('validates customer details, places a COD order, and navigates to private tracking', async () => {
    const checkout = vi.spyOn(storeApi, 'checkout').mockResolvedValue(placedOrder);
    render(
      <MemoryRouter initialEntries={['/s/demo-shop/checkout']}>
        <Routes>
          <Route path="/s/:storeSlug/checkout" element={<CheckoutPage />} />
          <Route path="/s/:storeSlug/cart" element={<LocationProbe />} />
          <Route path="/s/:storeSlug/orders/:orderCode" element={<LocationProbe />} />
        </Routes>
      </MemoryRouter>,
    );

    fireEvent.change(screen.getByLabelText('Full name'), { target: { value: 'Example Buyer' } });
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'buyer@example.test' } });
    fireEvent.change(screen.getByLabelText('Phone'), { target: { value: '+8801712345678' } });
    fireEvent.change(screen.getByLabelText('City'), { target: { value: 'Dhaka' } });
    fireEvent.change(screen.getByLabelText('Street address and area'), {
      target: { value: '12 Example Road, Dhanmondi' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Place COD order/ }));

    await waitFor(() => expect(checkout).toHaveBeenCalledOnce());
    expect(checkout).toHaveBeenCalledWith(
      'demo-shop',
      expect.objectContaining({
        email: 'buyer@example.test',
        full_name: 'Example Buyer',
        items: [{ variant_id: 10, quantity: 1 }],
      }),
      expect.any(String),
    );
    await waitFor(() =>
      expect(screen.getByTestId('location').textContent).toBe(
        `/s/demo-shop/orders/DK-TESTORDER#token=${placedOrder.tracking_token}`,
      ),
    );
    expect(useCart.getState().items).toEqual([]);
    checkout.mockRestore();
  });
});
