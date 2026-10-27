import { useState, type FormEvent, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { formatMoney } from '../storefront/components';
import { merchantApi } from '../lib/api';
import type { MerchantOrder, MerchantProductDetail, MerchantProductStatus } from '../lib/api';
import { PageFrame } from './pages';

type WorkspaceSection = 'overview' | 'products' | 'orders' | 'settings';

function WorkspaceNav({ storeId, active }: { storeId: number; active: WorkspaceSection }) {
  const items: Array<[WorkspaceSection, string, string]> = [
    ['overview', 'Overview', `/dashboard/stores/${storeId}`],
    ['products', 'Products', `/dashboard/stores/${storeId}/products`],
    ['orders', 'Orders', `/dashboard/stores/${storeId}/orders`],
    ['settings', 'Store settings', `/dashboard/stores/${storeId}/settings`],
  ];
  return <nav aria-label="Store workspace" className="mt-6 flex gap-1 overflow-x-auto rounded-xl border border-stone-200 bg-white p-1">{items.map(([key, label, href]) => <Link key={key} to={href} aria-current={key === active ? 'page' : undefined} className={`shrink-0 rounded-lg px-4 py-2.5 text-sm font-semibold transition ${key === active ? 'bg-stone-950 text-white' : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950'}`}>{label}</Link>)}</nav>;
}

function WorkspacePage({ title, section, children }: { title: string; section: WorkspaceSection; children: ReactNode }) {
  const { storeId: rawId = '' } = useParams();
  const storeId = Number(rawId);
  const stores = useQuery({ queryKey: ['merchant-stores'], queryFn: merchantApi.stores, retry: false });
  const store = stores.data?.find((item) => item.id === storeId);
  if (stores.isPending) return <PageFrame title={title}><p className="mt-6 text-stone-500">Loading your store…</p></PageFrame>;
  if (stores.error) return <PageFrame title={title}><p className="mt-6 rounded-xl bg-white p-5">Sign in to manage your store. <Link to="/dashboard/login" className="font-semibold underline">Sign in</Link></p></PageFrame>;
  if (!store) return <PageFrame title={title}><p className="mt-6 rounded-xl bg-white p-5">This store isn’t available to your account. <Link to="/dashboard" className="font-semibold underline">Back to your stores</Link></p></PageFrame>;
  return <PageFrame title={title}><WorkspaceNav storeId={storeId} active={section} /><div className="mt-6">{children}</div></PageFrame>;
}

interface ProductFormValues {
  title: string;
  description: string;
  sku: string;
  price: string;
  quantity: string;
  status: MerchantProductStatus;
}

function ProductForm({
  product,
  reservedQuantity,
  onCancel,
  onSave,
  saving,
  error,
}: {
  product: MerchantProductDetail | null;
  reservedQuantity: number;
  onCancel: () => void;
  onSave: (values: ProductFormValues) => void;
  saving: boolean;
  error: string;
}) {
  const variant = product?.variants[0];
  const [values, setValues] = useState<ProductFormValues>({
    title: product?.title ?? '',
    description: product?.description ?? '',
    sku: variant?.sku ?? '',
    price: variant ? (variant.price_minor / 100).toFixed(2) : '',
    quantity: String(variant?.quantity_on_hand ?? 0),
    status: product?.status ?? 'published',
  });
  const set = (key: keyof ProductFormValues, value: string) => setValues((current) => ({ ...current, [key]: value }));
  return (
    <form onSubmit={(event: FormEvent<HTMLFormElement>) => { event.preventDefault(); onSave(values); }} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-7">
      <div className="flex items-start justify-between gap-4"><div><h2 className="font-display text-xl font-bold">{product ? 'Edit product' : 'Add a product'}</h2><p className="mt-1 text-sm text-stone-500">Add the product and its first option. You can change its visibility any time.</p></div><button type="button" onClick={onCancel} className="rounded-lg px-3 py-2 text-sm font-semibold text-stone-600 hover:bg-stone-100">Close</button></div>
      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <label className="block text-sm font-medium sm:col-span-2">Product name<input autoFocus required maxLength={200} value={values.title} onChange={(event) => set('title', event.target.value)} className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" placeholder="e.g. Hand-thrown breakfast bowl" /></label>
        <label className="block text-sm font-medium sm:col-span-2">Description <span className="font-normal text-stone-500">(optional)</span><textarea rows={3} maxLength={5000} value={values.description} onChange={(event) => set('description', event.target.value)} className="mt-1.5 w-full resize-y rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" placeholder="Tell customers what makes it special." /></label>
        <label className="block text-sm font-medium">SKU<input required maxLength={64} value={values.sku} onChange={(event) => set('sku', event.target.value.toUpperCase())} className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" placeholder="e.g. BOWL-01" /></label>
        <label className="block text-sm font-medium">Price (BDT)<input required type="number" min="0" step="0.01" value={values.price} onChange={(event) => set('price', event.target.value)} className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" placeholder="850.00" /></label>
        <label className="block text-sm font-medium">Quantity in stock<input required type="number" min={reservedQuantity} step="1" value={values.quantity} onChange={(event) => set('quantity', event.target.value)} className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /><span className="mt-1 block text-xs font-normal text-stone-500">{reservedQuantity ? `${reservedQuantity} reserved for open orders.` : 'You can adjust stock later.'}</span></label>
        <label className="block text-sm font-medium">Storefront visibility<select value={values.status} onChange={(event) => set('status', event.target.value)} className="mt-1.5 w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200"><option value="published">Visible to customers</option><option value="draft">Keep as draft</option><option value="archived">Archived</option></select></label>
      </div>
      {error && <p role="alert" className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
      <div className="mt-6 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"><button type="button" onClick={onCancel} className="rounded-lg border border-stone-300 px-4 py-2.5 text-sm font-semibold">Cancel</button><button disabled={saving} className="rounded-lg bg-stone-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-stone-700 disabled:opacity-50">{saving ? 'Saving product…' : product ? 'Save changes' : 'Save product'}</button></div>
    </form>
  );
}

export function ProductManagementPage() {
  const { storeId: rawId = '' } = useParams();
  const storeId = Number(rawId);
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<'all' | MerchantProductStatus>('all');
  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [creating, setCreating] = useState(false);
  const [saveError, setSaveError] = useState('');
  const products = useQuery({ queryKey: ['products', storeId], queryFn: () => merchantApi.products(storeId), enabled: storeId > 0 });
  const inventory = useQuery({ queryKey: ['inventory', storeId], queryFn: () => merchantApi.inventory(storeId), enabled: storeId > 0 });
  const editQuery = useQuery({ queryKey: ['product-detail', storeId, editingId], queryFn: () => merchantApi.product(storeId, editingId!), enabled: editingId !== null });
  const editProduct = editQuery.data ?? null;
  const save = useMutation({
    mutationFn: async (input: { values: ProductFormValues; product: MerchantProductDetail | null }) => {
      const { values, product } = input;
      const price = Math.round(Number(values.price) * 100);
      const quantity = Math.trunc(Number(values.quantity));
      if (!Number.isFinite(price) || price < 0 || !Number.isInteger(quantity) || quantity < 0) throw new Error('Enter a valid price and stock quantity.');
      const savedProduct = product
        ? await merchantApi.updateProduct(storeId, product.id, { title: values.title.trim(), description: values.description.trim() || null })
        : await merchantApi.createProduct(storeId, { title: values.title.trim(), description: values.description.trim() || null });
      const variant = product?.variants[0];
      const savedVariant = variant
        ? await merchantApi.updateVariant(storeId, savedProduct.id, variant.id, { sku: values.sku.trim(), title: variant.title || 'Default', price_minor: price, currency: 'BDT' })
        : await merchantApi.createVariant(storeId, savedProduct.id, { sku: values.sku.trim(), title: 'Default', price_minor: price, currency: 'BDT', options: {} });
      const currentQuantity = variant?.quantity_on_hand ?? 0;
      const delta = quantity - currentQuantity;
      if (delta !== 0) await merchantApi.adjustInventory(storeId, savedVariant.id, delta, product ? 'Updated from product editor' : 'Initial stock from product setup');
      await merchantApi.updateProduct(storeId, savedProduct.id, { status: values.status });
      return savedProduct;
    },
    onSuccess: async () => {
      setSaveError('');
      setCreating(false);
      setEditingId(null);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['products', storeId] }),
        queryClient.invalidateQueries({ queryKey: ['inventory', storeId] }),
        queryClient.invalidateQueries({ queryKey: ['analytics', storeId] }),
        queryClient.invalidateQueries({ queryKey: ['store-products'] }),
      ]);
    },
    onError: (error) => setSaveError(error.message),
  });
  const normalizedSearch = search.trim().toLowerCase();
  const visibleProducts = (products.data ?? []).filter((product) =>
    (statusFilter === 'all' || product.status === statusFilter) && product.title.toLowerCase().includes(normalizedSearch),
  );
  const stockByProduct = new Map<number, number>();
  for (const row of inventory.data ?? []) stockByProduct.set(row.product_id, (stockByProduct.get(row.product_id) ?? 0) + row.quantity_on_hand);
  const activeEditor = creating || editingId !== null;
  const openEditor = (productId: number | null) => {
    setSaveError('');
    if (productId === null) { setCreating(true); setEditingId(null); }
    else { setCreating(false); setEditingId(productId); }
  };
  const closeEditor = () => { setCreating(false); setEditingId(null); setSaveError(''); };
  return <WorkspacePage title="Products" section="products">
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm text-stone-500">Your catalog</p><h2 className="mt-1 font-display text-2xl font-bold">Products</h2></div><button onClick={() => openEditor(null)} className="rounded-lg bg-stone-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-stone-700">+ Add product</button></div>
    {activeEditor && (editingId !== null && editQuery.isPending ? <div className="mt-5 rounded-xl border border-stone-200 bg-white p-6 text-sm text-stone-500">Loading product…</div> : editingId !== null && !editProduct ? <div className="mt-5 rounded-xl bg-rose-50 p-4 text-sm text-rose-800">Couldn’t load this product. <button onClick={closeEditor} className="font-semibold underline">Close</button></div> : <div className="mt-5"><ProductForm key={editProduct?.id ?? 'new'} product={editProduct} reservedQuantity={editProduct?.variants[0]?.reserved_quantity ?? 0} onCancel={closeEditor} saving={save.isPending} error={saveError} onSave={(values) => save.mutate({ values, product: editProduct })} /></div>)}
    <div className="mt-6 flex flex-col gap-3 sm:flex-row"><label className="flex-1"><span className="sr-only">Search products</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products" className="w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /></label><label><span className="sr-only">Filter product visibility</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)} className="w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5 sm:w-48"><option value="all">All products</option><option value="published">Visible</option><option value="draft">Drafts</option><option value="archived">Archived</option></select></label></div>
    {products.isPending ? <p className="mt-6 text-sm text-stone-500">Loading products…</p> : products.error ? <p role="alert" className="mt-6 rounded-xl bg-rose-50 p-4 text-sm text-rose-800">Products could not be loaded. Your account may not have catalog access.</p> : visibleProducts.length ? <div className="mt-4 overflow-hidden rounded-2xl border border-stone-200 bg-white"><div className="hidden grid-cols-[minmax(0,1fr)_120px_120px_120px] gap-4 bg-stone-50 px-5 py-3 text-xs font-semibold uppercase tracking-wide text-stone-500 sm:grid"><span>Product</span><span>Visibility</span><span>In stock</span><span className="text-right">Action</span></div>{visibleProducts.map((product) => <div key={product.id} className="grid gap-3 border-t border-stone-100 px-5 py-4 sm:grid-cols-[minmax(0,1fr)_120px_120px_120px] sm:items-center"><div className="min-w-0"><p className="truncate font-semibold">{product.title}</p><p className="mt-1 text-xs text-stone-500">{product.description || 'No description yet'}</p></div><span className={`w-fit rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${product.status === 'published' ? 'bg-emerald-50 text-emerald-800' : product.status === 'draft' ? 'bg-amber-50 text-amber-800' : 'bg-stone-100 text-stone-600'}`}>{product.status === 'published' ? 'Visible' : product.status}</span><span className="text-sm text-stone-600">{stockByProduct.get(product.id) ?? 0} units</span><button onClick={() => openEditor(product.id)} className="rounded-lg border border-stone-300 px-3 py-2 text-sm font-semibold transition hover:border-stone-950">Edit product</button></div>)}</div> : <div className="mt-5 rounded-2xl border border-dashed border-stone-300 bg-white p-8 text-center"><h3 className="font-display text-xl font-bold">{search || statusFilter !== 'all' ? 'No products match these filters' : 'Your catalog is ready for its first product'}</h3><p className="mt-2 text-sm text-stone-600">{search || statusFilter !== 'all' ? 'Try a different search or visibility filter.' : 'Add a product, price, and stock quantity to show it in your storefront.'}</p>{!search && statusFilter === 'all' && <button onClick={() => openEditor(null)} className="mt-4 rounded-lg bg-stone-950 px-4 py-2.5 text-sm font-semibold text-white">Add your first product</button>}</div>}
  </WorkspacePage>;
}

function orderTransitions(status: MerchantOrder['status']): MerchantOrder['status'][] {
  const transitions: Partial<Record<MerchantOrder['status'], MerchantOrder['status'][]>> = {
    pending: ['confirmed', 'cancelled'],
    confirmed: ['shipped', 'cancelled'],
    shipped: ['delivered'],
  };
  return transitions[status] ?? [];
}

export function OrderManagementPage() {
  const { storeId: rawId = '' } = useParams();
  const storeId = Number(rawId);
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<'all' | MerchantOrder['status']>('all');
  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(null);
  const orders = useQuery({ queryKey: ['merchant-orders', storeId, statusFilter], queryFn: () => merchantApi.orders(storeId, statusFilter === 'all' ? undefined : statusFilter), enabled: storeId > 0 });
  const detail = useQuery({ queryKey: ['merchant-order', storeId, selectedOrderId], queryFn: () => merchantApi.order(storeId, selectedOrderId!), enabled: selectedOrderId !== null });
  const updateStatus = useMutation({
    mutationFn: ({ orderId, status }: { orderId: number; status: MerchantOrder['status'] }) => merchantApi.updateOrderStatus(storeId, orderId, status),
    onSuccess: async (updated) => {
      await queryClient.invalidateQueries({ queryKey: ['merchant-orders', storeId] });
      await queryClient.invalidateQueries({ queryKey: ['merchant-order', storeId, updated.id] });
    },
  });
  const visibleOrders = orders.data ?? [];
  return <WorkspacePage title="Orders" section="orders">
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between"><div><p className="text-sm text-stone-500">Fulfillment</p><h2 className="mt-1 font-display text-2xl font-bold">Orders</h2></div><label><span className="sr-only">Filter order status</span><select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)} className="rounded-lg border border-stone-300 bg-white px-3 py-2.5"><option value="all">All statuses</option><option value="pending">Pending</option><option value="confirmed">Confirmed</option><option value="shipped">Shipped</option><option value="delivered">Delivered</option><option value="cancelled">Cancelled</option></select></label></div>
    {orders.isPending ? <p className="mt-6 text-sm text-stone-500">Loading orders…</p> : orders.error ? <p role="alert" className="mt-6 rounded-xl bg-rose-50 p-4 text-sm text-rose-800">Orders could not be loaded. Your account may not have order access.</p> : visibleOrders.length ? <div className="mt-5 overflow-hidden rounded-2xl border border-stone-200 bg-white">{visibleOrders.map((order) => <div key={order.id} className="flex flex-col gap-3 border-b border-stone-100 p-4 last:border-0 sm:flex-row sm:items-center sm:justify-between sm:px-5"><button onClick={() => setSelectedOrderId(order.id)} className="min-w-0 text-left"><span className="block font-semibold underline decoration-stone-300 underline-offset-4">{order.order_code}</span><span className="mt-1 block truncate text-sm text-stone-600">{order.customer_name} · {order.customer_email}</span><span className="mt-1 block text-xs text-stone-500">{new Date(order.created_at).toLocaleString()} · {order.items.length} {order.items.length === 1 ? 'item' : 'items'}</span></button><div className="flex items-center justify-between gap-4 sm:justify-end"><span className="font-semibold">{formatMoney(order.total_minor, order.currency)}</span>{orderTransitions(order.status).length ? <select aria-label={`Update ${order.order_code} status`} value={order.status} disabled={updateStatus.isPending} onChange={(event) => updateStatus.mutate({ orderId: order.id, status: event.target.value as MerchantOrder['status'] })} className="rounded-lg border border-stone-300 bg-white px-2 py-2 text-sm"><option value={order.status}>{order.status}</option>{orderTransitions(order.status).map((status) => <option key={status} value={status}>{status}</option>)}</select> : <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs font-semibold capitalize text-stone-600">{order.status}</span>}<button onClick={() => setSelectedOrderId(order.id)} className="text-sm font-semibold text-stone-700 underline underline-offset-4">Details</button></div></div>)}</div> : <div className="mt-5 rounded-2xl border border-dashed border-stone-300 bg-white p-8 text-center"><h3 className="font-display text-xl font-bold">No {statusFilter === 'all' ? '' : `${statusFilter} `}orders yet</h3><p className="mt-2 text-sm text-stone-600">New customer orders will show up here.</p></div>}
    {updateStatus.error && <p role="alert" className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{updateStatus.error.message}</p>}
    {selectedOrderId !== null && <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-stone-950/50 p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) setSelectedOrderId(null); }}><section role="dialog" aria-modal="true" aria-labelledby="order-detail-title" className="my-8 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-5 shadow-2xl sm:p-7"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wide text-stone-500">Order details</p><h2 id="order-detail-title" className="mt-1 font-display text-2xl font-bold">{detail.data?.order_code ?? 'Order'}</h2></div><button onClick={() => setSelectedOrderId(null)} className="rounded-lg px-3 py-2 text-sm font-semibold hover:bg-stone-100">Close</button></div>{detail.isPending ? <p className="py-8 text-sm text-stone-500">Loading order details…</p> : detail.error || !detail.data ? <p role="alert" className="mt-5 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">Order details could not be loaded.</p> : <><div className="mt-5 grid gap-4 rounded-xl bg-stone-50 p-4 sm:grid-cols-2"><div><p className="text-xs uppercase tracking-wide text-stone-500">Customer</p><p className="mt-1 font-semibold">{detail.data.shipping_name}</p><p className="text-sm text-stone-600">{detail.data.customer_email}</p><p className="text-sm text-stone-600">{detail.data.shipping_phone}</p></div><div><p className="text-xs uppercase tracking-wide text-stone-500">Delivery address</p><p className="mt-1 text-sm leading-6 text-stone-700">{detail.data.shipping_address}<br />{detail.data.shipping_city}{detail.data.shipping_postal_code ? ` ${detail.data.shipping_postal_code}` : ''}<br />{detail.data.shipping_country}</p></div></div><div className="mt-5 divide-y divide-stone-100">{detail.data.items.map((item) => <div key={item.sku} className="flex justify-between gap-4 py-3 text-sm"><span>{item.quantity} × {item.product_title}<span className="block text-xs text-stone-500">{item.variant_title} · {item.sku}</span></span><span className="shrink-0">{formatMoney(item.line_total_minor, detail.data.currency)}</span></div>)}</div><div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-stone-200 pt-4"><div><p className="font-semibold">Total {formatMoney(detail.data.total_minor, detail.data.currency)}</p><p className="mt-1 text-xs text-stone-500">Cash on delivery · {detail.data.payment_status}</p></div><span className="rounded-full bg-lime-100 px-3 py-1.5 text-sm font-semibold capitalize">{detail.data.status}</span></div><p className="mt-4 text-xs text-stone-500">Placed {new Date(detail.data.created_at).toLocaleString()}</p></>}</section></div>}
  </WorkspacePage>;
}

function StoreSettingsForm({ store, storeId }: { store: { name: string; slug: string; status: string }; storeId: number }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(store.name);
  const [slug, setSlug] = useState(store.slug);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const update = useMutation({
    mutationFn: () => merchantApi.updateStore(storeId, { name: name.trim(), slug: slug.trim().toLowerCase() }),
    onSuccess: async () => {
      setError('');
      setSaved(true);
      await queryClient.invalidateQueries({ queryKey: ['merchant-stores'] });
    },
    onError: (reason) => { setSaved(false); setError(reason.message); },
  });
  return <form onSubmit={(event) => { event.preventDefault(); setSaved(false); update.mutate(); }} className="max-w-2xl rounded-2xl border border-stone-200 bg-white p-5 shadow-sm sm:p-7"><div><p className="text-sm text-stone-500">Store profile</p><h2 className="mt-1 font-display text-2xl font-bold">Store settings</h2><p className="mt-2 text-sm leading-6 text-stone-600">Update your shop’s display name and its customer link.</p></div><label className="mt-6 block text-sm font-medium">Store name<input required maxLength={100} value={name} onChange={(event) => setName(event.target.value)} className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /></label><label className="mt-4 block text-sm font-medium">Store link<div className="mt-1.5 flex overflow-hidden rounded-lg border border-stone-300 focus-within:border-stone-950 focus-within:ring-2 focus-within:ring-stone-200"><span className="flex items-center bg-stone-50 px-3 text-sm text-stone-500">/s/</span><input required minLength={3} maxLength={63} pattern="[a-z0-9]+(-[a-z0-9]+)*" value={slug} onChange={(event) => setSlug(event.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))} className="min-w-0 flex-1 px-3 py-2.5 outline-none" /></div><span className="mt-1 block text-xs font-normal text-stone-500">Changing this link means old links to your shop will stop working.</span></label><div className="mt-5 flex flex-wrap items-center gap-3"><button disabled={update.isPending || !name.trim() || !slug.trim()} className="rounded-lg bg-stone-950 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-stone-700 disabled:opacity-50">{update.isPending ? 'Saving…' : 'Save settings'}</button><span className="text-sm text-stone-500">Store status: <strong className="capitalize text-stone-700">{store.status}</strong></span></div>{error && <p role="alert" className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}{saved && <p role="status" className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">Your store settings have been saved.</p>}</form>;
}

export function StoreSettingsPage() {
  const { storeId: rawId = '' } = useParams();
  const storeId = Number(rawId);
  const stores = useQuery({ queryKey: ['merchant-stores'], queryFn: merchantApi.stores, retry: false });
  const store = stores.data?.find((item) => item.id === storeId);
  return <WorkspacePage title="Store settings" section="settings">{stores.isPending ? <p className="text-sm text-stone-500">Loading settings…</p> : stores.error ? <p role="alert" className="rounded-xl bg-rose-50 p-4 text-sm text-rose-800">You must sign in to update store settings.</p> : !store ? <p className="rounded-xl bg-white p-5 text-sm text-stone-600">Store not found. <Link to="/dashboard" className="font-semibold underline">Back to your stores</Link></p> : <StoreSettingsForm key={store.id} store={store} storeId={storeId} />}</WorkspacePage>;
}
