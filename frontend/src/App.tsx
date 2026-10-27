import { Route, Routes } from 'react-router-dom';
import {
  CartPage,
  CheckoutPage,
  LandingPage,
  OrderConfirmationPage,
  ProductPage,
  ShopDirectoryPage,
  StorefrontHome,
  StoreShell,
} from './storefront/pages';
import {
  DashboardLoginPage,
  DashboardRegisterPage,
  MerchantDashboardPage,
  MerchantStoreDashboardPage,
  PlatformAdminPage,
} from './dashboard/pages';
import {
  OrderManagementPage,
  ProductManagementPage,
  StoreSettingsPage,
} from './dashboard/management-pages';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/shops" element={<ShopDirectoryPage />} />
      <Route path="/dashboard/login" element={<DashboardLoginPage />} />
      <Route path="/dashboard/register" element={<DashboardRegisterPage />} />
      <Route path="/dashboard" element={<MerchantDashboardPage />} />
      <Route path="/dashboard/stores/:storeId" element={<MerchantStoreDashboardPage />} />
      <Route path="/dashboard/stores/:storeId/products" element={<ProductManagementPage />} />
      <Route path="/dashboard/stores/:storeId/orders" element={<OrderManagementPage />} />
      <Route path="/dashboard/stores/:storeId/settings" element={<StoreSettingsPage />} />
      <Route path="/platform-admin" element={<PlatformAdminPage />} />
      <Route path="/s/:storeSlug" element={<StoreShell />}>
        <Route index element={<StorefrontHome />} />
        <Route path="products/:productId" element={<ProductPage />} />
        <Route path="cart" element={<CartPage />} />
        <Route path="checkout" element={<CheckoutPage />} />
        <Route path="orders/:orderCode" element={<OrderConfirmationPage />} />
      </Route>
      <Route path="*" element={<LandingPage />} />
    </Routes>
  );
}
