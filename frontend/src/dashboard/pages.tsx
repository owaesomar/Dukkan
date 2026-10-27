import { useState, type FormEvent } from 'react';
import type { ReactNode } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { merchantApi, platformAdminApi } from '../lib/api';
import type { MerchantOrder, StoreMember, SubscriptionPlan } from '../lib/api';
import { formatMoney } from '../storefront/components';

const roles: StoreMember['role'][] = ['admin', 'manager', 'catalog', 'fulfillment', 'staff', 'viewer'];

export function PageFrame({ title, children }: { title: string; children: ReactNode }) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const profile = useQuery({ queryKey: ['merchant-me'], queryFn: merchantApi.me, retry: false });
  const logout = useMutation({
    mutationFn: merchantApi.logout,
    onSuccess: () => {
      queryClient.clear();
      navigate('/dashboard/login');
    },
  });
  return (
    <main className="min-h-screen bg-stone-100 text-stone-950">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <Link to="/dashboard" className="font-display text-xl font-bold">Dukkan <span className="text-sm font-medium text-stone-400">Merchant</span></Link>
          <nav className="flex items-center gap-3 text-sm sm:gap-5"><Link className="text-stone-600 hover:text-stone-950" to="/">Home</Link><Link className="text-stone-600 hover:text-stone-950" to="/platform-admin">Platform admin</Link>{profile.data && <button type="button" disabled={logout.isPending} onClick={() => logout.mutate()} className="font-semibold text-stone-700 underline underline-offset-4 disabled:opacity-50">{logout.isPending ? 'Signing out…' : 'Sign out'}</button>}</nav>
        </div>
      </header>
      <div className="mx-auto max-w-6xl px-5 py-8 sm:py-12">
        <h1 className="font-display text-3xl font-bold">{title}</h1>
        {children}
      </div>
    </main>
  );
}

export function DashboardLoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  const login = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) => merchantApi.login(email, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['merchant-me'], user);
      navigate('/dashboard');
    },
    onError: (reason) => setError(reason.message),
  });
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    const form = new FormData(event.currentTarget);
    login.mutate({ email: String(form.get('email')), password: String(form.get('password')) });
  };
  return (
    <PageFrame title="Sign in to your shop">
      <form onSubmit={submit} className="mt-6 max-w-md space-y-4 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-stone-600">Manage your store, orders, and team from one place.</p>
        <label className="block text-sm font-medium">Email address<input name="email" type="email" required autoComplete="email" className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /></label>
        <label className="block text-sm font-medium">Password<input name="password" type="password" required autoComplete="current-password" className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /></label>
        {error && <p role="alert" className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <button disabled={login.isPending} className="w-full rounded-lg bg-stone-950 px-4 py-3 font-semibold text-white transition hover:bg-stone-700 disabled:opacity-50">{login.isPending ? 'Signing in…' : 'Sign in'}</button>
        <p className="text-center text-sm text-stone-600">New to Dukkan? <Link to="/dashboard/register" className="font-semibold text-stone-950 underline underline-offset-4">Create an account</Link></p>
      </form>
    </PageFrame>
  );
}

export function DashboardRegisterPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  const register = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) => merchantApi.register(email, password),
    onSuccess: (user) => {
      queryClient.setQueryData(['merchant-me'], user);
      navigate('/dashboard');
    },
    onError: (reason) => setError(reason.message),
  });
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    const form = new FormData(event.currentTarget);
    const password = String(form.get('password'));
    if (password !== String(form.get('confirm_password'))) {
      setError('Those passwords do not match. Please try again.');
      return;
    }
    register.mutate({ email: String(form.get('email')).trim(), password });
  };
  return (
    <PageFrame title="Start your shop">
      <form onSubmit={submit} className="mt-6 max-w-md space-y-4 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm">
        <p className="text-sm leading-6 text-stone-600">Create your account, choose a store name, and you’ll be ready to set up your shop.</p>
        <label className="block text-sm font-medium">Email address<input name="email" type="email" required autoComplete="email" className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /></label>
        <label className="block text-sm font-medium">Password<input name="password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" aria-describedby="password-help" className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /><span id="password-help" className="mt-1 block text-xs font-normal text-stone-500">Use at least 12 characters.</span></label>
        <label className="block text-sm font-medium">Confirm password<input name="confirm_password" type="password" required minLength={12} maxLength={128} autoComplete="new-password" className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /></label>
        {error && <p role="alert" className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
        <button disabled={register.isPending} className="w-full rounded-lg bg-stone-950 px-4 py-3 font-semibold text-white transition hover:bg-stone-700 disabled:opacity-50">{register.isPending ? 'Creating account…' : 'Create account'}</button>
        <p className="text-center text-sm text-stone-600">Already have an account? <Link to="/dashboard/login" className="font-semibold text-stone-950 underline underline-offset-4">Sign in</Link></p>
      </form>
    </PageFrame>
  );
}

export function MerchantDashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [error, setError] = useState('');
  const [storeName, setStoreName] = useState('');
  const [storeSlug, setStoreSlug] = useState('');
  const [slugEdited, setSlugEdited] = useState(false);
  const profile = useQuery({ queryKey: ['merchant-me'], queryFn: merchantApi.me, retry: false });
  const stores = useQuery({ queryKey: ['merchant-stores'], queryFn: merchantApi.stores, retry: false });
  const create = useMutation({
    mutationFn: ({ name, slug }: { name: string; slug: string }) => merchantApi.createStore(name, slug),
    onSuccess: (store) => {
      void queryClient.invalidateQueries({ queryKey: ['merchant-stores'] });
      navigate(`/dashboard/stores/${store.id}`);
    },
    onError: (reason) => setError(reason.message),
  });
  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    create.mutate({ name: storeName.trim(), slug: storeSlug.trim().toLowerCase() });
  };
  if (profile.isPending || stores.isPending) return <PageFrame title="Your stores"><p className="mt-6 text-stone-500">Loading your workspace…</p></PageFrame>;
  if (profile.error || stores.error) return <PageFrame title="Your stores"><div className="mt-6 rounded-2xl bg-white p-6"><p className="text-stone-600">Sign in to manage your stores.</p><Link to="/dashboard/login" className="mt-4 inline-block rounded-lg bg-stone-950 px-4 py-2.5 font-semibold text-white">Sign in</Link></div></PageFrame>;
  return (
    <PageFrame title={`Welcome, ${profile.data.email}`}>
      <div className="mt-7 grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
        <section className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-7">
          <h2 className="font-display text-xl font-bold">Stores you can manage</h2>
          {stores.data.length ? <div className="mt-4 divide-y divide-stone-100">{stores.data.map((store) => <Link key={store.id} to={`/dashboard/stores/${store.id}`} className="flex items-center justify-between py-4"><span><span className="block font-semibold">{store.name}</span><span className="text-sm text-stone-500">/s/{store.slug}</span></span><span className="text-sm font-medium">Open dashboard →</span></Link>)}</div> : <p className="mt-4 text-sm text-stone-500">You do not have a store yet.</p>}
        </section>
        <form onSubmit={submit} className="h-fit rounded-2xl border border-stone-200 bg-white p-5 sm:p-7">
          <h2 className="font-display text-xl font-bold">Create your store</h2>
          <p className="mt-2 text-sm text-stone-600">Choose a name and a short link customers can remember.</p>
          <label className="mt-4 block text-sm font-medium">Store name<input name="name" value={storeName} onChange={(event) => { const name = event.target.value; setStoreName(name); if (!slugEdited) setStoreSlug(name.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')); }} required maxLength={100} className="mt-1.5 w-full rounded-lg border border-stone-300 px-3 py-2.5 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /></label>
          <label className="mt-4 block text-sm font-medium">Your store link<div className="mt-1.5 flex overflow-hidden rounded-lg border border-stone-300 focus-within:border-stone-950 focus-within:ring-2 focus-within:ring-stone-200"><span className="flex items-center bg-stone-50 px-3 text-sm text-stone-500">/s/</span><input name="slug" value={storeSlug} onChange={(event) => { setSlugEdited(true); setStoreSlug(event.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '')); }} required minLength={3} pattern="[a-z0-9]+(-[a-z0-9]+)*" className="min-w-0 flex-1 px-3 py-2.5 outline-none" /></div><span className="mt-1 block text-xs font-normal text-stone-500">Lowercase letters, numbers, and hyphens. You can change this later.</span></label>
          {(error || create.error) && <p role="alert" className="mt-3 text-sm text-rose-700">{error || create.error?.message}</p>}
          <button disabled={create.isPending || !storeName.trim() || !storeSlug.trim()} className="mt-5 w-full rounded-lg bg-stone-950 px-4 py-3 font-semibold text-white transition hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-50">{create.isPending ? 'Creating your store…' : 'Create store'}</button>
        </form>
      </div>
    </PageFrame>
  );
}

export function MerchantStoreDashboardPage() {
  const { storeId: rawId = '' } = useParams();
  const storeId = Number(rawId);
  const queryClient = useQueryClient();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const profile = useQuery({ queryKey: ['merchant-me'], queryFn: merchantApi.me, retry: false });
  const stores = useQuery({ queryKey: ['merchant-stores'], queryFn: merchantApi.stores, retry: false });
  const store = stores.data?.find((item) => item.id === storeId);
  const analytics = useQuery({ queryKey: ['analytics', storeId], queryFn: () => merchantApi.analytics(storeId), enabled: Number.isInteger(storeId) && storeId > 0 });
  const orders = useQuery({ queryKey: ['merchant-orders', storeId], queryFn: () => merchantApi.orders(storeId), enabled: Number.isInteger(storeId) && storeId > 0 });
  const members = useQuery({ queryKey: ['members', storeId], queryFn: () => merchantApi.members(storeId), enabled: Number.isInteger(storeId) && storeId > 0 });
  const subscription = useQuery({ queryKey: ['subscription', storeId], queryFn: () => merchantApi.subscription(storeId), enabled: Number.isInteger(storeId) && storeId > 0 });
  const plans = useQuery({ queryKey: ['subscription-plans'], queryFn: merchantApi.plans });
  const myRole = members.data?.find((member) => member.user_id === profile.data?.id)?.role;
  const canManage = myRole === 'owner' || myRole === 'admin';
  const refreshStore = () => {
    void queryClient.invalidateQueries({ queryKey: ['members', storeId] });
    void queryClient.invalidateQueries({ queryKey: ['subscription', storeId] });
  };
  const addMember = useMutation({
    mutationFn: ({ email, role }: { email: string; role: StoreMember['role'] }) => merchantApi.addMember(storeId, email, role),
    onSuccess: () => { setMessage('Team member added.'); setError(''); refreshStore(); },
    onError: (reason) => setError(reason.message),
  });
  const updateMember = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: StoreMember['role'] }) => merchantApi.updateMember(storeId, userId, role),
    onSuccess: refreshStore,
    onError: (reason) => setError(reason.message),
  });
  const removeMember = useMutation({
    mutationFn: (userId: number) => merchantApi.removeMember(storeId, userId),
    onSuccess: refreshStore,
    onError: (reason) => setError(reason.message),
  });
  const setPlan = useMutation({
    mutationFn: (planId: number) => merchantApi.setPlan(storeId, planId),
    onSuccess: refreshStore,
    onError: (reason) => setError(reason.message),
  });
  const cancelPlan = useMutation({
    mutationFn: () => merchantApi.cancelSubscription(storeId, 'Canceled by store owner from dashboard'),
    onSuccess: refreshStore,
    onError: (reason) => setError(reason.message),
  });
  const updateOrder = useMutation({
    mutationFn: ({ id, status }: { id: number; status: MerchantOrder['status'] }) => merchantApi.updateOrderStatus(storeId, id, status),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ['merchant-orders', storeId] }); void queryClient.invalidateQueries({ queryKey: ['analytics', storeId] }); },
    onError: (reason) => setError(reason.message),
  });
  const invite = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    addMember.mutate({ email: String(form.get('email')), role: String(form.get('role')) as StoreMember['role'] });
    event.currentTarget.reset();
  };
  if (stores.isPending || profile.isPending) return <PageFrame title="Store dashboard"><p className="mt-6 text-stone-500">Loading…</p></PageFrame>;
  if (stores.error || profile.error) return <PageFrame title="Store dashboard"><p className="mt-6">Sign in to continue. <Link className="underline" to="/dashboard/login">Sign in</Link></p></PageFrame>;
  if (!store) return <PageFrame title="Store dashboard"><p className="mt-6">Store not found or you do not have access. <Link className="underline" to="/dashboard">Back to stores</Link></p></PageFrame>;
  const cards = analytics.data ? [
    ['Orders', analytics.data.orders_count],
    ['Open orders', analytics.data.open_orders_count],
    ['Units sold', analytics.data.units_sold],
    ['New customers', analytics.data.new_customers_count],
    ['Published products', analytics.data.published_products_count],
    ['Low stock variants', analytics.data.low_stock_variants_count],
  ] as const : [];
  return (
    <PageFrame title={store.name}>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-stone-500"><Link to="/dashboard" className="underline">All stores</Link><span>/</span><a href={`/s/${store.slug}`} className="underline">View storefront</a><span>Analytics cover the last 30 days.</span></div>
      <nav aria-label="Store workspace" className="mt-6 flex gap-1 overflow-x-auto rounded-xl border border-stone-200 bg-white p-1">{[['Overview', `/dashboard/stores/${storeId}`, true], ['Products', `/dashboard/stores/${storeId}/products`, false], ['Orders', `/dashboard/stores/${storeId}/orders`, false], ['Store settings', `/dashboard/stores/${storeId}/settings`, false]].map(([label, href, active]) => <Link key={String(label)} to={String(href)} aria-current={active ? 'page' : undefined} className={`shrink-0 rounded-lg px-4 py-2.5 text-sm font-semibold transition ${active ? 'bg-stone-950 text-white' : 'text-stone-600 hover:bg-stone-100 hover:text-stone-950'}`}>{String(label)}</Link>)}</nav>
      {analytics.data && <section aria-label="Store analytics" className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{cards.map(([label, value]) => <article key={label} className="rounded-2xl border border-stone-200 bg-white p-5"><p className="text-sm text-stone-500">{label}</p><p className="mt-2 font-display text-3xl font-bold">{value}</p></article>)}{Object.entries(analytics.data.paid_revenue_by_currency).map(([currency, amount]) => <article key={currency} className="rounded-2xl border border-stone-200 bg-white p-5"><p className="text-sm text-stone-500">Paid revenue</p><p className="mt-2 font-display text-3xl font-bold">{formatMoney(amount, currency)}</p></article>)}</section>}
      {analytics.error && <p role="alert" className="mt-5 rounded-xl bg-rose-50 p-4 text-sm text-rose-800">Analytics could not be loaded: {analytics.error.message}</p>}
      <div className="mt-7 grid gap-6 xl:grid-cols-2">
        <section className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-7 xl:col-span-2">
          <div className="flex items-center justify-between gap-3"><h2 className="font-display text-xl font-bold">Recent orders</h2><Link to={`/dashboard/stores/${storeId}/orders`} className="text-sm font-semibold underline underline-offset-4">View all orders</Link></div>
          {orders.data?.length ? <div className="mt-4 divide-y divide-stone-100">{orders.data.map((order) => {
            const nextStatuses: Partial<Record<MerchantOrder['status'], MerchantOrder['status'][]>> = {
              pending: ['confirmed', 'cancelled'], confirmed: ['shipped', 'cancelled'], shipped: ['delivered'],
            };
            return <div key={order.id} className="grid gap-3 py-4 sm:grid-cols-[1fr_1fr_auto] sm:items-center"><div><p className="font-semibold">{order.order_code} · {order.customer_name}</p><p className="text-sm text-stone-500">{order.customer_email} · {new Date(order.created_at).toLocaleDateString()}</p><p className="mt-1 text-xs text-stone-500">{order.items.map((item) => `${item.quantity} × ${item.product_title}`).join(', ')}</p></div><p className="text-sm font-semibold">{formatMoney(order.total_minor, order.currency)} · <span className="font-normal capitalize text-stone-500">{order.payment_status}</span></p>{(myRole === 'owner' || myRole === 'admin' || myRole === 'manager' || myRole === 'fulfillment' || myRole === 'staff') && nextStatuses[order.status]?.length ? <select aria-label={`Update ${order.order_code}`} value="" onChange={(event) => event.target.value && updateOrder.mutate({ id: order.id, status: event.target.value as MerchantOrder['status'] })} className="rounded-lg border border-stone-300 px-2 py-2 text-sm"><option value="">{order.status}</option>{nextStatuses[order.status]?.map((next) => <option key={next} value={next}>{next}</option>)}</select> : <span className="text-sm capitalize text-stone-500">{order.status}</span>}</div>;
          })}</div> : <p className="mt-3 text-sm text-stone-500">No orders in this store yet.</p>}
          {orders.error && <p className="mt-3 text-sm text-stone-500">You do not have permission to view orders.</p>}
        </section>
        <section className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-7">
          <div className="flex items-start justify-between"><div><h2 className="font-display text-xl font-bold">Team access</h2><p className="mt-1 text-sm text-stone-500">Give teammates the access they need for this store.</p></div><span className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold capitalize">{myRole ?? 'No access'}</span></div>
          {members.data && <div className="mt-4 divide-y divide-stone-100">{members.data.map((member) => <div key={member.user_id} className="flex flex-wrap items-center justify-between gap-3 py-3"><div><p className="font-medium">{member.email}</p><p className="text-xs text-stone-500">{member.role}{member.is_active ? '' : ' · inactive'}</p></div>{canManage && member.is_active && member.role !== 'owner' && <div className="flex items-center gap-2"><select aria-label={`Role for ${member.email}`} value={member.role} onChange={(event) => updateMember.mutate({ userId: member.user_id, role: event.target.value as StoreMember['role'] })} className="rounded-lg border border-stone-300 px-2 py-1.5 text-sm">{roles.map((role) => <option key={role} value={role}>{role}</option>)}</select><button onClick={() => removeMember.mutate(member.user_id)} className="text-sm text-rose-700 underline">Remove</button></div>}</div>)}</div>}
          {canManage && <div className="mt-5 border-t border-stone-100 pt-5"><p className="mb-3 text-xs leading-5 text-stone-500">Ask each teammate to create their own Dukkan account at <span className="font-medium text-stone-700">/dashboard/register</span>, then add the email they registered with.</p><form onSubmit={invite} className="grid gap-2 sm:grid-cols-[1fr_150px_auto]"><input name="email" type="email" required placeholder="Teammate’s account email" aria-label="Teammate account email" className="rounded-lg border border-stone-300 px-3 py-2 outline-none focus:border-stone-950 focus:ring-2 focus:ring-stone-200"/><select name="role" defaultValue="staff" aria-label="Team member role" className="rounded-lg border border-stone-300 px-3 py-2">{roles.map((role) => <option key={role} value={role}>{role.charAt(0).toUpperCase() + role.slice(1)}</option>)}</select><button disabled={addMember.isPending} className="rounded-lg bg-stone-950 px-4 py-2 font-semibold text-white transition hover:bg-stone-700 disabled:opacity-50">{addMember.isPending ? 'Adding…' : 'Add teammate'}</button></form></div>}
          {members.error && <p className="mt-4 text-sm text-stone-500">You may not have permission to view team access.</p>}
        </section>
        <section className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-7">
          <h2 className="font-display text-xl font-bold">Subscription</h2>
          {subscription.data ? <div className="mt-4 rounded-xl bg-stone-50 p-4"><p className="font-semibold">{subscription.data.plan.name} · <span className="capitalize">{subscription.data.status}</span></p><p className="mt-1 text-sm text-stone-600">{formatMoney(subscription.data.plan.price_minor, subscription.data.plan.currency)} / {subscription.data.plan.billing_interval}</p><p className="mt-2 text-xs text-stone-500">Plan status is managed here; payment collection is not connected yet.</p></div> : <p className="mt-4 text-sm text-stone-500">{subscription.error ? 'You do not have permission to view billing.' : 'No plan selected.'}</p>}
          {canManage && plans.data && <div className="mt-4 flex flex-wrap gap-2"><select aria-label="Choose a plan" id="plan-choice" defaultValue={subscription.data?.plan.id ?? ''} className="rounded-lg border border-stone-300 px-3 py-2">{!subscription.data && <option value="" disabled>Select a plan</option>}{plans.data.map((plan) => <option key={plan.id} value={plan.id}>{plan.name} · {formatMoney(plan.price_minor, plan.currency)} / {plan.billing_interval}</option>)}</select><button onClick={() => { const selection = document.getElementById('plan-choice') as HTMLSelectElement; if (selection.value) setPlan.mutate(Number(selection.value)); }} className="rounded-lg bg-stone-950 px-4 py-2 font-semibold text-white">Save plan</button>{subscription.data?.status === 'active' && <button onClick={() => cancelPlan.mutate()} className="rounded-lg border border-rose-200 px-4 py-2 text-rose-700">Cancel plan</button>}</div>}
        </section>
      </div>
      {(error || message) && <p role={error ? 'alert' : 'status'} className={`mt-5 rounded-xl p-3 text-sm ${error ? 'bg-rose-50 text-rose-800' : 'bg-emerald-50 text-emerald-800'}`}>{error || message}</p>}
    </PageFrame>
  );
}

export function PlatformAdminPage() {
  const queryClient = useQueryClient();
  const overview = useQuery({ queryKey: ['platform-overview'], queryFn: platformAdminApi.overview, retry: false });
  const merchants = useQuery({ queryKey: ['platform-merchants'], queryFn: platformAdminApi.merchants, retry: false });
  const stores = useQuery({ queryKey: ['platform-stores'], queryFn: platformAdminApi.stores, retry: false });
  const plans = useQuery({ queryKey: ['platform-plans'], queryFn: platformAdminApi.plans, retry: false });
  const subscriptions = useQuery({ queryKey: ['platform-subscriptions'], queryFn: platformAdminApi.subscriptions, retry: false });
  const audit = useQuery({ queryKey: ['platform-audit'], queryFn: platformAdminApi.auditEvents, retry: false });
  const [error, setError] = useState('');
  const refresh = () => Promise.all([
    queryClient.invalidateQueries({ queryKey: ['platform-overview'] }),
    queryClient.invalidateQueries({ queryKey: ['platform-stores'] }),
    queryClient.invalidateQueries({ queryKey: ['platform-merchants'] }),
    queryClient.invalidateQueries({ queryKey: ['platform-subscriptions'] }),
    queryClient.invalidateQueries({ queryKey: ['platform-audit'] }),
  ]);
  const storeStatus = useMutation({ mutationFn: ({ id, status }: { id: number; status: 'active' | 'suspended' | 'disabled' }) => platformAdminApi.updateStoreStatus(id, status), onSuccess: refresh, onError: (reason) => setError(reason.message) });
  const planMutation = useMutation({
    mutationFn: (data: Omit<SubscriptionPlan, 'id' | 'created_at' | 'updated_at' | 'is_active'>) => platformAdminApi.createPlan(data),
    onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ['platform-plans'] }); setError(''); },
    onError: (reason) => setError(reason.message),
  });
  const setMerchantActive = useMutation({ mutationFn: ({ userId, active }: { userId: number; active: boolean }) => platformAdminApi.updateMerchantStatus(userId, active), onSuccess: refresh, onError: (reason) => setError(reason.message) });
  const togglePlan = useMutation({ mutationFn: ({ planId, active }: { planId: number; active: boolean }) => platformAdminApi.setPlanActive(planId, active), onSuccess: () => { void queryClient.invalidateQueries({ queryKey: ['platform-plans'] }); }, onError: (reason) => setError(reason.message) });
  const createPlan = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    planMutation.mutate({
      code: String(form.get('code')),
      name: String(form.get('name')),
      description: String(form.get('description')) || null,
      price_minor: Number(form.get('price_minor')),
      currency: String(form.get('currency')),
      billing_interval: String(form.get('billing_interval')) as SubscriptionPlan['billing_interval'],
      limits: {},
    });
    event.currentTarget.reset();
  };
  if (overview.isPending) return <PageFrame title="Platform administration"><p className="mt-6 text-stone-500">Loading platform data…</p></PageFrame>;
  if (overview.error) return <PageFrame title="Platform administration"><p className="mt-6 rounded-xl bg-white p-5">Platform administrator access is required. <Link to="/dashboard/login" className="underline">Sign in</Link></p></PageFrame>;
  return (
    <PageFrame title="Platform administration">
      <p className="mt-2 text-sm text-stone-500">Global access is separate from store membership. Changes are recorded in the audit log.</p>
      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">{[['Merchants', overview.data.users_count], ['Stores', overview.data.stores_count], ['Active stores', overview.data.active_stores_count], ['Orders', overview.data.orders_count], ['Subscriptions', overview.data.subscriptions_count]].map(([name, value]) => <div key={name} className="rounded-2xl border border-stone-200 bg-white p-5"><p className="text-sm text-stone-500">{name}</p><p className="mt-2 text-3xl font-bold">{value}</p></div>)}{Object.entries(overview.data.monthly_recurring_revenue_by_currency).map(([currency, amount]) => <div key={currency} className="rounded-2xl border border-stone-200 bg-white p-5"><p className="text-sm text-stone-500">Est. monthly recurring revenue</p><p className="mt-2 text-3xl font-bold">{formatMoney(amount, currency)}</p></div>)}</div>
      <div className="mt-7 grid gap-6 xl:grid-cols-2">
        <section className="rounded-2xl border border-stone-200 bg-white p-5"><h2 className="font-display text-xl font-bold">Stores</h2><div className="mt-3 divide-y divide-stone-100">{stores.data?.map((store) => <div key={store.id} className="flex flex-wrap items-center justify-between gap-3 py-3"><div><p className="font-semibold">{store.name} <span className="font-normal text-stone-500">/{store.slug}</span></p><p className="text-xs text-stone-500">{store.owner_email ?? 'No owner'} · {store.members_count} team members · {store.status}</p></div><select aria-label={`Status for ${store.name}`} value={store.status} onChange={(event) => storeStatus.mutate({ id: store.id, status: event.target.value as 'active' | 'suspended' | 'disabled' })} className="rounded-lg border border-stone-300 px-2 py-1.5 text-sm"><option value="active">Active</option><option value="suspended">Suspended</option><option value="disabled">Disabled</option></select></div>)}</div></section>
        <section className="rounded-2xl border border-stone-200 bg-white p-5"><h2 className="font-display text-xl font-bold">Merchants</h2><div className="mt-3 divide-y divide-stone-100">{merchants.data?.map((merchant) => <div key={merchant.user_id} className="flex items-center justify-between gap-3 py-3"><span><span className="block font-medium">{merchant.email}</span><span className="text-xs text-stone-500">{merchant.stores_count} stores · {merchant.is_active ? 'active' : 'suspended'}</span></span><button onClick={() => setMerchantActive.mutate({ userId: merchant.user_id, active: !merchant.is_active })} className="text-sm underline">{merchant.is_active ? 'Suspend account' : 'Reactivate'}</button></div>)}</div></section>
        <section className="rounded-2xl border border-stone-200 bg-white p-5"><h2 className="font-display text-xl font-bold">Subscription plans</h2><div className="mt-3 divide-y divide-stone-100">{plans.data?.map((plan) => <div key={plan.id} className="flex items-center justify-between gap-3 py-3"><p><span className="font-semibold">{plan.name}</span><span className="ml-2 text-sm text-stone-500">{formatMoney(plan.price_minor, plan.currency)} / {plan.billing_interval} · {plan.is_active ? 'available' : 'archived'}</span></p><button onClick={() => togglePlan.mutate({ planId: plan.id, active: !plan.is_active })} className="text-sm underline">{plan.is_active ? 'Archive' : 'Restore'}</button></div>)}</div><form onSubmit={createPlan} className="mt-3 grid gap-2 border-t border-stone-100 pt-4 sm:grid-cols-2"><input name="code" required pattern="[a-z0-9]+(-[a-z0-9]+)*" placeholder="Plan code" className="rounded-lg border border-stone-300 px-3 py-2"/><input name="name" required placeholder="Plan name" className="rounded-lg border border-stone-300 px-3 py-2"/><input name="price_minor" type="number" min="0" required placeholder="Price in minor units" className="rounded-lg border border-stone-300 px-3 py-2"/><select name="currency" className="rounded-lg border border-stone-300 px-3 py-2"><option value="BDT">BDT</option><option value="USD">USD</option></select><select name="billing_interval" className="rounded-lg border border-stone-300 px-3 py-2"><option value="monthly">Monthly</option><option value="yearly">Yearly</option></select><input name="description" placeholder="Description (optional)" className="rounded-lg border border-stone-300 px-3 py-2"/><button className="rounded-lg bg-stone-950 px-4 py-2 font-semibold text-white sm:col-span-2">Add plan</button></form></section>
        <section className="rounded-2xl border border-stone-200 bg-white p-5"><h2 className="font-display text-xl font-bold">Subscriptions and activity</h2><div className="mt-3 divide-y divide-stone-100">{subscriptions.data?.map((subscription) => <p key={subscription.store_id} className="py-3 text-sm"><strong>{subscription.store_name}</strong> · {subscription.plan_name} · {subscription.status}</p>)}</div><h3 className="mt-5 font-semibold">Recent platform actions</h3><div className="mt-2 divide-y divide-stone-100">{audit.data?.slice(0, 8).map((event) => <p key={event.id} className="py-2 text-xs text-stone-600">{new Date(event.created_at).toLocaleString()} · {event.action} · {event.resource_type} {event.resource_id}</p>)}</div></section>
      </div>
      {error && <p role="alert" className="mt-5 rounded-xl bg-rose-50 p-3 text-sm text-rose-800">{error}</p>}
    </PageFrame>
  );
}
