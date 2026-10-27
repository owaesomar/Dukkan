import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { merchantApi } from '../lib/api';
import { DashboardLoginPage } from './pages';

describe('merchant dashboard entry', () => {
  it('logs in and opens the merchant workspace', async () => {
    const login = vi.spyOn(merchantApi, 'login').mockResolvedValue({
      id: 7,
      email: 'merchant@example.test',
      created_at: '2026-10-27T00:00:00Z',
    });
    const queryClient = new QueryClient({ defaultOptions: { mutations: { retry: false } } });
    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/dashboard/login']}>
          <Routes>
            <Route path="/dashboard/login" element={<DashboardLoginPage />} />
            <Route path="/dashboard" element={<p>Merchant workspace</p>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    );

    fireEvent.change(screen.getByLabelText('Email address'), {
      target: { value: 'merchant@example.test' },
    });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => expect(login).toHaveBeenCalledWith('merchant@example.test', 'password123'));
    expect(await screen.findByText('Merchant workspace')).toBeInTheDocument();
    login.mockRestore();
  });
});
