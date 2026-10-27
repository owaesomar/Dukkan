export interface PublicStore {
  id: number;
  slug: string;
  name: string;
}

export interface StoreCategory {
  id: number;
  name: string;
  slug: string;
}

export interface StoreVariant {
  id: number;
  sku: string;
  title: string;
  price_minor: number;
  currency: string;
  options: Record<string, string>;
  available_quantity: number;
}

export interface StoreMedia {
  id: number;
  alt_text: string;
  position: number;
  image_url: string | null;
}

export interface StoreProduct {
  id: number;
  title: string;
  description: string | null;
  category_id: number | null;
  variants: StoreVariant[];
  media: StoreMedia[];
}

export interface CheckoutInput {
  email: string;
  full_name: string;
  phone: string;
  shipping_address: string;
  city: string;
  postal_code?: string;
  country: string;
  items: Array<{ variant_id: number; quantity: number }>;
}

export interface CheckoutResult {
  order_code: string;
  status: string;
  payment_method: string;
  payment_status: string;
  subtotal_minor: number;
  shipping_minor: number;
  total_minor: number;
  currency: string;
  tracking_token: string;
  items: Array<{
    product_title: string;
    variant_title: string;
    sku: string;
    quantity: number;
    unit_price_minor: number;
    line_total_minor: number;
  }>;
}

export interface TrackedOrder {
  order_code: string;
  status: string;
  payment_method: string;
  payment_status: string;
  total_minor: number;
  currency: string;
  created_at: string;
  items: CheckoutResult['items'];
}

export interface UserProfile {
  id: number;
  email: string;
  created_at: string;
}

export interface MerchantStore {
  id: number;
  name: string;
  slug: string;
  status: string;
  created_at: string;
}

export type MerchantProductStatus = 'draft' | 'published' | 'archived';

export interface MerchantProduct {
  id: number;
  store_id: number;
  category_id: number | null;
  title: string;
  description: string | null;
  status: MerchantProductStatus;
  created_at: string;
  updated_at: string;
}

export interface MerchantProductVariant {
  id: number;
  store_id: number;
  product_id: number;
  sku: string;
  title: string;
  price_minor: number;
  currency: string;
  options: Record<string, string>;
  is_active: boolean;
  quantity_on_hand: number;
  reserved_quantity: number;
  created_at: string;
}

export interface MerchantProductDetail extends MerchantProduct {
  variants: MerchantProductVariant[];
  media: Array<{ id: number; alt_text: string; position: number; content_type: string; byte_size: number; created_at: string }>;
}

export interface InventoryItem {
  store_id: number;
  variant_id: number;
  sku: string;
  product_id: number;
  product_title: string;
  quantity_on_hand: number;
  reserved_quantity: number;
  updated_at: string;
}

export interface InventoryAdjustment {
  id: number;
  store_id: number;
  variant_id: number;
  actor_user_id: number;
  delta: number;
  reason: string;
  created_at: string;
}

export interface StoreAnalytics {
  period_start: string;
  period_end: string;
  orders_count: number;
  open_orders_count: number;
  delivered_orders_count: number;
  units_sold: number;
  paid_revenue_by_currency: Record<string, number>;
  new_customers_count: number;
  published_products_count: number;
  low_stock_variants_count: number;
}

export interface StoreMember {
  store_id: number;
  user_id: number;
  email: string;
  role: 'owner' | 'admin' | 'manager' | 'catalog' | 'fulfillment' | 'staff' | 'viewer';
  is_active: boolean;
  created_at: string;
}

export interface SubscriptionPlan {
  id: number;
  code: string;
  name: string;
  description: string | null;
  price_minor: number;
  currency: string;
  billing_interval: 'monthly' | 'yearly';
  limits: Record<string, number>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StoreSubscription {
  store_id: number;
  plan: SubscriptionPlan;
  status: 'active' | 'past_due' | 'canceled';
  cancellation_reason: string | null;
  started_at: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
  updated_at: string;
}

export interface MerchantOrder {
  id: number;
  customer_id: number;
  customer_email: string;
  customer_name: string;
  shipping_name: string;
  shipping_phone: string;
  shipping_address: string;
  shipping_city: string;
  shipping_postal_code: string | null;
  shipping_country: string;
  order_code: string;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  payment_method: 'cash_on_delivery';
  payment_status: 'unpaid' | 'paid';
  total_minor: number;
  currency: string;
  created_at: string;
  items: CheckoutResult['items'];
}

export interface PlatformOverview {
  users_count: number;
  stores_count: number;
  active_stores_count: number;
  suspended_stores_count: number;
  orders_count: number;
  subscriptions_count: number;
  monthly_recurring_revenue_by_currency: Record<string, number>;
}

export interface PlatformStore extends MerchantStore {
  owner_email: string | null;
  members_count: number;
}

export interface PlatformMerchant {
  user_id: number;
  email: string;
  is_active: boolean;
  stores_count: number;
  created_at: string;
}

export interface PlatformSubscription {
  store_id: number;
  store_name: string;
  store_slug: string;
  plan_id: number;
  plan_code: string;
  plan_name: string;
  price_minor: number;
  currency: string;
  billing_interval: 'monthly' | 'yearly';
  status: 'active' | 'past_due' | 'canceled';
  cancellation_reason: string | null;
  started_at: string;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export interface PlatformAuditEvent {
  id: number;
  actor_user_id: number;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  created_at: string;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...init,
    headers: { Accept: 'application/json', ...init?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function csrfHeader(): Record<string, string> {
  const cookie = document.cookie.split('; ').find((part) => part.startsWith('dukkan_csrf='));
  return cookie ? { 'X-CSRF-Token': decodeURIComponent(cookie.slice('dukkan_csrf='.length)) } : {};
}

function jsonMutation<T>(url: string, method: 'POST' | 'PUT' | 'PATCH', data: unknown) {
  return request<T>(url, {
    method,
    headers: { 'Content-Type': 'application/json', ...csrfHeader() },
    body: JSON.stringify(data),
  });
}

const publicPath = (slug: string) => `/api/v1/public/stores/${encodeURIComponent(slug)}`;

export const storeApi = {
  listStores: () => request<PublicStore[]>('/api/v1/public/stores'),
  getStore: (slug: string) => request<PublicStore>(publicPath(slug)),
  getCategories: (slug: string) => request<StoreCategory[]>(`${publicPath(slug)}/categories`),
  getProducts: (slug: string, q = '', categoryId = '') => {
    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (categoryId) params.set('category_id', categoryId);
    const suffix = params.size ? `?${params.toString()}` : '';
    return request<StoreProduct[]>(`${publicPath(slug)}/products${suffix}`);
  },
  getProduct: (slug: string, productId: string) =>
    request<StoreProduct>(`${publicPath(slug)}/products/${productId}`),
  checkout: (slug: string, input: CheckoutInput, idempotencyKey: string) =>
    request<CheckoutResult>(`${publicPath(slug)}/checkout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify(input),
    }),
  trackOrder: (slug: string, orderCode: string, token: string) =>
    request<TrackedOrder>(`${publicPath(slug)}/orders/${encodeURIComponent(orderCode)}`, {
      headers: { 'X-Order-Tracking-Token': token },
    }),
};

export const merchantApi = {
  me: () => request<UserProfile>('/api/v1/auth/me'),
  register: (email: string, password: string) =>
    jsonMutation<UserProfile>('/api/v1/auth/register', 'POST', { email, password }),
  login: (email: string, password: string) => jsonMutation<UserProfile>('/api/v1/auth/login', 'POST', { email, password }),
  logout: () => request<void>('/api/v1/auth/logout', { method: 'POST', headers: csrfHeader() }),
  stores: () => request<MerchantStore[]>('/api/v1/stores'),
  createStore: (name: string, slug: string) => jsonMutation<MerchantStore>('/api/v1/stores', 'POST', { name, slug }),
  updateStore: (storeId: number, changes: { name?: string; slug?: string }) =>
    jsonMutation<MerchantStore>(`/api/v1/stores/${storeId}`, 'PATCH', changes),
  analytics: (storeId: number) => request<StoreAnalytics>(`/api/v1/stores/${storeId}/analytics/overview`),
  orders: (storeId: number, status?: MerchantOrder['status']) => {
    const suffix = status ? `?status_filter=${encodeURIComponent(status)}` : '';
    return request<MerchantOrder[]>(`/api/v1/stores/${storeId}/orders${suffix}`);
  },
  order: (storeId: number, orderId: number) => request<MerchantOrder>(`/api/v1/stores/${storeId}/orders/${orderId}`),
  updateOrderStatus: (storeId: number, orderId: number, status: MerchantOrder['status']) =>
    jsonMutation<MerchantOrder>(`/api/v1/stores/${storeId}/orders/${orderId}/status`, 'PATCH', { status }),
  members: (storeId: number) => request<StoreMember[]>(`/api/v1/stores/${storeId}/members`),
  addMember: (storeId: number, email: string, role: StoreMember['role']) =>
    jsonMutation<StoreMember>(`/api/v1/stores/${storeId}/members`, 'POST', { email, role }),
  updateMember: (storeId: number, userId: number, role: StoreMember['role']) =>
    jsonMutation<StoreMember>(`/api/v1/stores/${storeId}/members/${userId}`, 'PATCH', { role }),
  removeMember: (storeId: number, userId: number) =>
    request<void>(`/api/v1/stores/${storeId}/members/${userId}`, { method: 'DELETE', headers: csrfHeader() }),
  subscription: (storeId: number) => request<StoreSubscription | null>(`/api/v1/stores/${storeId}/subscription`),
  plans: () => request<SubscriptionPlan[]>('/api/v1/subscription-plans'),
  setPlan: (storeId: number, planId: number) =>
    jsonMutation<StoreSubscription>(`/api/v1/stores/${storeId}/subscription`, 'PUT', { plan_id: planId }),
  cancelSubscription: (storeId: number, reason: string) =>
    jsonMutation<StoreSubscription>(`/api/v1/stores/${storeId}/subscription/cancel`, 'POST', { reason }),
  products: (storeId: number) => request<MerchantProduct[]>(`/api/v1/stores/${storeId}/products`),
  product: (storeId: number, productId: number) => request<MerchantProductDetail>(`/api/v1/stores/${storeId}/products/${productId}`),
  createProduct: (storeId: number, product: { title: string; description: string | null }) =>
    jsonMutation<MerchantProduct>(`/api/v1/stores/${storeId}/products`, 'POST', product),
  updateProduct: (storeId: number, productId: number, changes: { title?: string; description?: string | null; status?: MerchantProductStatus }) =>
    jsonMutation<MerchantProduct>(`/api/v1/stores/${storeId}/products/${productId}`, 'PATCH', changes),
  createVariant: (storeId: number, productId: number, variant: { sku: string; title: string; price_minor: number; currency: string; options: Record<string, string> }) =>
    jsonMutation<MerchantProductVariant>(`/api/v1/stores/${storeId}/products/${productId}/variants`, 'POST', variant),
  updateVariant: (storeId: number, productId: number, variantId: number, changes: { sku?: string; title?: string; price_minor?: number; currency?: string }) =>
    jsonMutation<MerchantProductVariant>(`/api/v1/stores/${storeId}/products/${productId}/variants/${variantId}`, 'PATCH', changes),
  inventory: (storeId: number) => request<InventoryItem[]>(`/api/v1/stores/${storeId}/inventory`),
  adjustInventory: (storeId: number, variantId: number, delta: number, reason: string) =>
    jsonMutation<InventoryAdjustment>(`/api/v1/stores/${storeId}/inventory/variants/${variantId}/adjustments`, 'POST', { delta, reason }),
};

export const platformAdminApi = {
  overview: () => request<PlatformOverview>('/api/v1/platform-admin/overview'),
  merchants: () => request<PlatformMerchant[]>('/api/v1/platform-admin/merchants'),
  stores: () => request<PlatformStore[]>('/api/v1/platform-admin/stores'),
  subscriptions: () => request<PlatformSubscription[]>('/api/v1/platform-admin/subscriptions'),
  plans: () => request<SubscriptionPlan[]>('/api/v1/platform-admin/plans'),
  auditEvents: () => request<PlatformAuditEvent[]>('/api/v1/platform-admin/audit-events'),
  createPlan: (plan: Omit<SubscriptionPlan, 'id' | 'created_at' | 'updated_at' | 'is_active'>) =>
    jsonMutation<SubscriptionPlan>('/api/v1/platform-admin/plans', 'POST', plan),
  setPlanActive: (planId: number, isActive: boolean) =>
    jsonMutation<SubscriptionPlan>(`/api/v1/platform-admin/plans/${planId}`, 'PATCH', { is_active: isActive }),
  updateStoreStatus: (storeId: number, next: 'active' | 'suspended' | 'disabled') =>
    jsonMutation<PlatformStore>(`/api/v1/platform-admin/stores/${storeId}/status`, 'PATCH', {
      status: next,
      reason: `Status changed to ${next} from platform dashboard`,
    }),
  updateMerchantStatus: (userId: number, isActive: boolean) =>
    jsonMutation<PlatformMerchant>(`/api/v1/platform-admin/merchants/${userId}/status`, 'PATCH', {
      is_active: isActive,
      reason: `Account ${isActive ? 'reactivated' : 'suspended'} from platform dashboard`,
    }),
};
