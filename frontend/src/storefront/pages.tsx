import { useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, Outlet, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { storeApi } from '../lib/api';
import type { CheckoutInput } from '../lib/api';
import { useCart } from './cart';
import type { CartLine } from './cart';
import { cartItem, formatMoney, ProductArtwork, ProductCard, StoreHeader } from './components';
import { demoShopImage } from './demo-art';

const EMPTY_CART: CartLine[] = [];

function ShopCard({ store }: { store: { id: number; slug: string; name: string } }) {
  const cover = demoShopImage(store.slug);
  return <Link to={`/s/${store.slug}`} className="group rounded-2xl border border-stone-200 bg-white p-4 transition hover:-translate-y-0.5 hover:border-stone-400 hover:shadow-lg hover:shadow-stone-900/5"><div className="relative grid aspect-[1.5] place-items-center overflow-hidden rounded-xl bg-gradient-to-br from-lime-100 to-orange-100">{cover ? <div aria-hidden="true" className="absolute inset-0 transition duration-500 group-hover:scale-105" style={{ backgroundImage: `url(${cover})`, backgroundSize: '100% 100%' }} /> : <span className="grid h-14 w-14 place-items-center rounded-2xl bg-white/80 font-display text-2xl font-bold text-stone-800 shadow-sm">{store.name.trim().charAt(0).toUpperCase()}</span>}<span className="absolute bottom-3 left-3 rounded-full bg-white/90 px-3 py-1 text-xs font-semibold text-stone-800">Independent shop</span></div><div className="mt-4 flex items-center justify-between gap-3"><div className="min-w-0"><h2 className="truncate font-display text-xl font-bold">{store.name}</h2><p className="mt-1 truncate text-sm text-stone-500">dukkan / {store.slug}</p></div><span aria-hidden="true" className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-stone-200 transition group-hover:border-stone-950 group-hover:bg-stone-950 group-hover:text-white">→</span></div></Link>;
}

const Field = ({ label, error, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { label: string; error?: string }) => (
  <label className="block">
    <span className="mb-1.5 block text-sm font-medium text-stone-700">{label}</span>
    <input className="w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5 outline-none transition focus:border-stone-950 focus:ring-2 focus:ring-stone-200" {...props} />
    {error && <span className="mt-1 block text-xs text-rose-700">{error}</span>}
  </label>
);

export function LandingPage() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#f8f8f4] text-stone-950">
      <header className="relative z-10 mx-auto flex max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Link to="/" className="flex items-center gap-3" aria-label="Dukkan home">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-stone-950 text-lg font-bold text-lime-300">D</span>
          <span className="font-display text-xl font-bold tracking-tight">Dukkan</span>
        </Link>
        <nav className="flex items-center gap-3 text-sm font-semibold sm:gap-6">
          <Link to="/shops" className="hidden text-stone-600 transition hover:text-stone-950 sm:inline">Browse shops</Link>
          <Link to="/dashboard/login" className="text-stone-600 transition hover:text-stone-950">Sign in</Link>
          <Link to="/dashboard/register" className="rounded-full bg-stone-950 px-4 py-2.5 text-white transition hover:bg-stone-700 sm:px-5">Open your shop</Link>
        </nav>
      </header>
      <section className="relative mx-auto grid max-w-7xl items-center gap-10 px-5 pb-16 pt-10 sm:px-8 sm:pb-24 sm:pt-16 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="relative z-10 max-w-2xl">
          <p className="inline-flex items-center gap-2 rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-stone-600"><span className="h-2 w-2 rounded-full bg-lime-500" /> Made for independent shops</p>
          <h1 className="mt-6 font-display text-5xl font-bold leading-[1.04] tracking-tight sm:text-6xl lg:text-7xl">Your next chapter starts <span className="text-stone-500">with a shop.</span></h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-stone-600">Bring your products, orders, and customers together in one simple place. Set up your storefront and start sharing it when you’re ready.</p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link to="/dashboard/register" className="inline-flex items-center justify-center gap-2 rounded-xl bg-stone-950 px-6 py-3.5 font-semibold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-stone-700">Create your shop <span aria-hidden="true">→</span></Link>
            <Link to="/dashboard/login" className="inline-flex items-center justify-center rounded-xl border border-stone-300 bg-white px-6 py-3.5 font-semibold transition hover:border-stone-500">I already have an account</Link>
          </div>
          <p className="mt-5 text-sm text-stone-500">Shopping for something? <Link to="/shops" className="font-semibold text-stone-800 underline underline-offset-2">Browse all shops</Link>.</p>
        </div>
        <div aria-hidden="true" className="relative mx-auto w-full max-w-xl lg:ml-auto">
          <div className="absolute -right-12 -top-12 h-56 w-56 rounded-full bg-lime-200/70 blur-3xl" />
          <div className="absolute -bottom-10 -left-12 h-48 w-48 rounded-full bg-orange-200/70 blur-3xl" />
          <div className="relative rotate-1 rounded-[2rem] border border-stone-200 bg-white p-3 shadow-2xl shadow-stone-900/10">
            <div className="overflow-hidden rounded-[1.45rem] bg-[#f2f0e9]">
              <div className="flex items-center justify-between border-b border-stone-200/80 bg-white px-5 py-4"><span className="font-display text-lg font-bold">Your shop</span><span className="rounded-full bg-lime-100 px-3 py-1 text-xs font-semibold text-lime-900">Open for business</span></div>
              <div className="p-5 sm:p-7">
                <div className="rounded-2xl bg-stone-950 px-5 py-7 text-white sm:px-7 sm:py-9"><p className="text-xs font-semibold uppercase tracking-[0.18em] text-lime-300">A little something special</p><p className="mt-3 max-w-xs font-display text-3xl font-bold leading-tight">Good things, picked with care.</p><p className="mt-3 text-sm text-stone-300">Your story. Your products. Your store.</p></div>
                <div className="mt-5 flex items-center justify-between"><div><p className="text-sm font-semibold">Featured collection</p><p className="mt-1 text-xs text-stone-500">Ready when you are</p></div><span className="grid h-9 w-9 place-items-center rounded-full bg-white text-lg">↗</span></div>
                <div className="mt-4 grid grid-cols-2 gap-3"><div className="aspect-[1.15] rounded-xl bg-gradient-to-br from-orange-100 to-rose-200" /><div className="aspect-[1.15] rounded-xl bg-gradient-to-br from-lime-100 to-emerald-200" /></div>
              </div>
            </div>
          </div>
          <div className="absolute -bottom-5 -left-3 rounded-2xl border border-stone-200 bg-white px-4 py-3 shadow-lg sm:-left-8"><p className="text-xs text-stone-500">Orders, all together</p><p className="mt-1 text-sm font-bold">One clear workspace</p></div>
        </div>
      </section>
      <section className="border-t border-stone-200 bg-white">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-12 sm:px-8 md:grid-cols-3 md:gap-10 md:py-16">
          {[['01', 'Create your account', 'Set up your shop profile in a few quick steps.'], ['02', 'Set up your shop', 'Choose a name and the link customers will use to find you.'], ['03', 'Keep things moving', 'Track orders, manage your team, and share your storefront.']].map(([number, title, copy]) => <article key={number} className="flex gap-4"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-lime-100 text-sm font-bold text-stone-900">{number}</span><div><h2 className="font-display text-lg font-bold">{title}</h2><p className="mt-2 text-sm leading-6 text-stone-600">{copy}</p></div></article>)}
        </div>
      </section>
    </main>
  );
}

export function ShopDirectoryPage() {
  const [search, setSearch] = useState('');
  const { data: stores, isPending, error, refetch, isFetching } = useQuery({
    queryKey: ['public-stores'],
    queryFn: storeApi.listStores,
  });
  const normalizedSearch = search.trim().toLocaleLowerCase();
  const visibleStores = (stores ?? []).filter((store) =>
    `${store.name} ${store.slug}`.toLocaleLowerCase().includes(normalizedSearch),
  );
  return (
    <main className="min-h-screen bg-[#f8f8f4] text-stone-950">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 sm:px-8">
          <Link to="/" className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-stone-950 font-bold text-lime-300">D</span><span className="font-display text-lg font-bold">Dukkan</span></Link>
          <Link to="/dashboard/register" className="rounded-full bg-stone-950 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-stone-700">Open your shop</Link>
        </div>
      </header>
      <div className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
          <div><Link to="/" className="text-sm font-medium text-stone-500 hover:text-stone-950">← Home</Link><p className="mt-6 text-xs font-bold uppercase tracking-[0.2em] text-stone-500">Independent shops</p><h1 className="mt-2 font-display text-4xl font-bold tracking-tight sm:text-5xl">Find your next favorite.</h1><p className="mt-3 max-w-xl text-stone-600">Browse every open shop and explore collections from independent merchants.</p></div>
          <label className="block w-full sm:max-w-xs"><span className="sr-only">Search shops</span><input type="search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search shops" className="w-full rounded-xl border border-stone-300 bg-white px-4 py-3 outline-none transition placeholder:text-stone-400 focus:border-stone-950 focus:ring-2 focus:ring-stone-200" /></label>
        </div>
        {isPending ? <div className="mt-10 rounded-2xl border border-stone-200 bg-white p-8 text-center text-stone-500" role="status">Loading shops…</div> : error ? <div className="mt-10 rounded-2xl border border-stone-200 bg-white p-8 text-center"><p className="font-semibold">Shops aren’t available right now.</p><p className="mt-2 text-sm text-stone-600">Please try again in a moment.</p><button onClick={() => void refetch()} disabled={isFetching} className="mt-4 rounded-lg bg-stone-950 px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50">{isFetching ? 'Trying again…' : 'Try again'}</button></div> : visibleStores.length ? <><p className="mt-10 text-sm text-stone-500" aria-live="polite">{visibleStores.length} {visibleStores.length === 1 ? 'shop' : 'shops'}</p><div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{visibleStores.map((store) => <ShopCard key={store.id} store={store} />)}</div></> : <div className="mt-10 rounded-2xl border border-dashed border-stone-300 bg-white p-10 text-center"><div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-lime-100 text-xl">⌕</div><h2 className="mt-4 font-display text-xl font-bold">{search ? 'No shops match that search' : 'New shops are on their way'}</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-stone-600">{search ? 'Try another name or clear your search to see every shop.' : 'Check back soon, or start your own shop and be one of the first to open.'}</p>{search ? <button onClick={() => setSearch('')} className="mt-4 text-sm font-semibold underline underline-offset-4">Clear search</button> : <Link to="/dashboard/register" className="mt-5 inline-flex rounded-lg bg-stone-950 px-4 py-2.5 text-sm font-semibold text-white">Create a shop</Link>}</div>}
      </div>
    </main>
  );
}

export function StoreShell() {
  const { storeSlug = '' } = useParams();
  const { data: store, isPending, error } = useQuery({
    queryKey: ['public-store', storeSlug],
    queryFn: () => storeApi.getStore(storeSlug),
  });
  if (isPending) return <PageMessage>Opening store…</PageMessage>;
  if (error || !store) return <PageMessage>We couldn’t find this store.</PageMessage>;
  return (
    <div className="min-h-screen bg-[#faf9f6] text-stone-950">
      <StoreHeader storeName={store.name} />
      <div className="mx-auto max-w-6xl px-5 py-8 sm:py-12"><Outlet /></div>
    </div>
  );
}

export function StorefrontHome() {
  const { storeSlug = '' } = useParams();
  const [params, setParams] = useSearchParams();
  const search = params.get('q') ?? '';
  const categoryId = params.get('category_id') ?? '';
  const { data: products, isPending, error } = useQuery({
    queryKey: ['store-products', storeSlug, search, categoryId],
    queryFn: () => storeApi.getProducts(storeSlug, search, categoryId),
  });
  const { data: categories } = useQuery({
    queryKey: ['store-categories', storeSlug],
    queryFn: () => storeApi.getCategories(storeSlug),
  });
  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next, { replace: true });
  };
  return (
    <>
      <section className="relative mb-10 overflow-hidden rounded-3xl bg-stone-950 px-6 py-10 text-white sm:px-10 sm:py-14">
        {demoShopImage(storeSlug) && <div aria-hidden="true" className="absolute inset-y-0 right-0 hidden w-1/2 opacity-35 sm:block" style={{ backgroundImage: `linear-gradient(90deg, #0c0a09 0%, transparent 65%), url(${demoShopImage(storeSlug)})`, backgroundPosition: 'center', backgroundSize: 'cover' }} />}
        <div className="relative z-10">
        <p className="text-xs font-bold uppercase tracking-[0.25em] text-lime-300">Independent shopping</p>
        <h1 className="mt-3 max-w-2xl font-display text-4xl font-bold leading-tight sm:text-5xl">Thoughtful finds, from a shop that feels like yours.</h1>
        <p className="mt-4 max-w-xl text-stone-300">Browse the collection and discover something made to stay.</p>
        </div>
      </section>
      <section aria-label="Product catalog">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div><p className="text-sm font-medium text-stone-500">The collection</p><h2 className="font-display text-2xl font-bold">Shop all</h2></div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <input aria-label="Search products" className="rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm" placeholder="Search products" value={search} onChange={(event) => setFilter('q', event.target.value)} />
            <select aria-label="Filter by category" className="rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm" value={categoryId} onChange={(event) => setFilter('category_id', event.target.value)}>
              <option value="">All categories</option>
              {categories?.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
            </select>
          </div>
        </div>
        {isPending ? <PageMessage>Loading the collection…</PageMessage> : error ? <PageMessage>Products are temporarily unavailable.</PageMessage> : products?.length ? (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">{products.map((product) => <ProductCard key={product.id} storeSlug={storeSlug} product={product} />)}</div>
        ) : <PageMessage>No products match this view yet.</PageMessage>}
      </section>
    </>
  );
}

export function ProductPage() {
  const { storeSlug = '', productId = '' } = useParams();
  const add = useCart((state) => state.add);
  const { data: product, isPending, error } = useQuery({
    queryKey: ['store-product', storeSlug, productId],
    queryFn: () => storeApi.getProduct(storeSlug, productId),
  });
  const [selectedVariant, setSelectedVariant] = useState<number | null>(null);
  if (isPending) return <PageMessage>Loading product…</PageMessage>;
  if (error || !product) return <PageMessage>This product isn’t available.</PageMessage>;
  const variant = product.variants.find((item) => item.id === selectedVariant) ?? product.variants[0];
  const image = product.media[0];
  return (
    <div>
      <Link className="text-sm text-stone-500 hover:text-stone-950" to={`/s/${storeSlug}`}>← Back to collection</Link>
      <div className="mt-6 grid gap-10 md:grid-cols-2">
        <div className="aspect-square overflow-hidden rounded-3xl bg-stone-100">
          {image?.image_url ? <img src={image.image_url} alt={image.alt_text || product.title} className="h-full w-full object-cover" /> : <ProductArtwork title={product.title} categoryId={product.category_id} storeSlug={storeSlug} />}
        </div>
        <div className="py-3">
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-stone-500">Store collection</p>
          <h1 className="mt-3 font-display text-4xl font-bold">{product.title}</h1>
          {variant && <p className="mt-4 text-xl">{formatMoney(variant.price_minor, variant.currency)}</p>}
          {product.description && <p className="mt-6 whitespace-pre-line leading-7 text-stone-600">{product.description}</p>}
          <div className="mt-8 space-y-3">
            {product.variants.map((item) => (
              <button key={item.id} onClick={() => setSelectedVariant(item.id)} className={`flex w-full items-center justify-between rounded-xl border p-4 text-left ${item.id === variant?.id ? 'border-stone-950 bg-white' : 'border-stone-200 bg-white/60'}`}>
                <span><span className="block font-semibold">{item.title}</span><span className="mt-1 block text-xs text-stone-500">{Object.entries(item.options).map(([key, value]) => `${key}: ${value}`).join(' · ') || item.sku}</span></span>
                <span className="text-right"><span className="block font-semibold">{formatMoney(item.price_minor, item.currency)}</span><span className="mt-1 block text-xs text-stone-500">{item.available_quantity > 0 ? `${item.available_quantity} available` : 'Sold out'}</span></span>
              </button>
            ))}
          </div>
          <button disabled={!variant || variant.available_quantity < 1} onClick={() => variant && add(storeSlug, cartItem(product, variant))} className="mt-5 w-full rounded-xl bg-stone-950 px-5 py-3.5 font-semibold text-white hover:bg-stone-700 disabled:cursor-not-allowed disabled:opacity-40">Add to bag</button>
        </div>
      </div>
    </div>
  );
}

export function CartPage() {
  const { storeSlug = '' } = useParams();
  const items = useCart((state) => state.storeSlug === storeSlug ? state.items : EMPTY_CART);
  const setQuantity = useCart((state) => state.setQuantity);
  const remove = useCart((state) => state.remove);
  const subtotal = useMemo(() => items.reduce((sum, item) => sum + item.priceMinor * item.quantity, 0), [items]);
  if (!items.length) return <PageMessage>Your bag is empty. <Link className="ml-1 font-semibold underline" to={`/s/${storeSlug}`}>Browse the collection</Link></PageMessage>;
  return (
    <section className="mx-auto max-w-3xl">
      <p className="text-sm text-stone-500">Your selection</p><h1 className="font-display text-3xl font-bold">Shopping bag</h1>
      <div className="mt-6 divide-y divide-stone-200 rounded-2xl border border-stone-200 bg-white px-5">
        {items.map((item) => <div key={item.variantId} className="flex gap-4 py-5">
          <div className="h-20 w-20 shrink-0 overflow-hidden rounded-xl bg-stone-100">{item.imageUrl && <img src={item.imageUrl} alt="" className="h-full w-full object-cover" />}</div>
          <div className="min-w-0 flex-1"><p className="truncate font-semibold">{item.productTitle}</p><p className="text-sm text-stone-500">{item.variantTitle} · {item.sku}</p><p className="mt-2 text-sm">{formatMoney(item.priceMinor, item.currency)}</p></div>
          <div className="flex flex-col items-end justify-between"><select aria-label={`Quantity for ${item.productTitle}`} value={item.quantity} onChange={(event) => setQuantity(item.variantId, Number(event.target.value))} className="rounded-lg border border-stone-300 px-2 py-1">{Array.from({ length: 20 }, (_, index) => <option key={index + 1} value={index + 1}>{index + 1}</option>)}</select><button onClick={() => remove(item.variantId)} className="text-xs text-stone-500 underline">Remove</button></div>
        </div>)}
      </div>
      <div className="mt-6 rounded-2xl bg-white p-5 shadow-sm"><div className="flex justify-between font-semibold"><span>Subtotal</span><span>{formatMoney(subtotal, items[0].currency)}</span></div><p className="mt-2 text-sm text-stone-500">Shipping is free. Pay cash when your order arrives.</p><Link to={`/s/${storeSlug}/checkout`} className="mt-5 block rounded-xl bg-stone-950 px-5 py-3.5 text-center font-semibold text-white hover:bg-stone-700">Continue to checkout</Link></div>
    </section>
  );
}

const checkoutSchema = z.object({
  full_name: z.string().trim().min(2, 'Enter your full name').max(160),
  email: z.string().trim().email('Enter a valid email address').max(320),
  phone: z.string().trim().min(7, 'Enter a valid phone number').max(32),
  shipping_address: z.string().trim().min(8, 'Enter your delivery address').max(1000),
  city: z.string().trim().min(2, 'Enter your city').max(100),
  postal_code: z.string().max(24).optional(),
  country: z.string().length(2).default('BD'),
});
type CheckoutFields = z.input<typeof checkoutSchema>;
type ValidCheckoutFields = z.output<typeof checkoutSchema>;

export function CheckoutPage() {
  const { storeSlug = '' } = useParams();
  const navigate = useNavigate();
  const items = useCart((state) => state.storeSlug === storeSlug ? state.items : EMPTY_CART);
  const clear = useCart((state) => state.clear);
  const [requestError, setRequestError] = useState('');
  const keyRef = useRef<{ fingerprint: string; key: string } | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<
    CheckoutFields,
    unknown,
    ValidCheckoutFields
  >({
    resolver: zodResolver(checkoutSchema),
    defaultValues: { country: 'BD' },
  });
  if (!items.length) return <PageMessage>Your bag is empty. <Link className="ml-1 font-semibold underline" to={`/s/${storeSlug}/cart`}>Return to your bag</Link></PageMessage>;
  const onSubmit = async (fields: ValidCheckoutFields) => {
    setRequestError('');
    const input: CheckoutInput = {
      ...fields,
      items: items.map(({ variantId, quantity }) => ({ variant_id: variantId, quantity })),
    };
    const fingerprint = JSON.stringify(input);
    if (!keyRef.current || keyRef.current.fingerprint !== fingerprint) {
      keyRef.current = { fingerprint, key: crypto.randomUUID() };
    }
    try {
      const order = await storeApi.checkout(storeSlug, input, keyRef.current.key);
      navigate(`/s/${storeSlug}/orders/${encodeURIComponent(order.order_code)}#token=${encodeURIComponent(order.tracking_token)}`);
      clear();
    } catch (error) {
      setRequestError(error instanceof Error ? error.message : 'Checkout failed. Please try again.');
    }
  };
  const total = items.reduce((sum, item) => sum + item.priceMinor * item.quantity, 0);
  const errorsFor = (key: keyof CheckoutFields) => errors[key]?.message as string | undefined;
  return (
    <div className="mx-auto grid max-w-5xl gap-8 lg:grid-cols-[1fr_360px]">
      <section>
        <Link className="text-sm text-stone-500 hover:text-stone-950" to={`/s/${storeSlug}/cart`}>← Back to bag</Link>
        <p className="mt-6 text-sm text-stone-500">Secure checkout</p><h1 className="font-display text-3xl font-bold">Delivery details</h1>
        <form className="mt-6 space-y-5 rounded-2xl border border-stone-200 bg-white p-5 sm:p-7" onSubmit={handleSubmit(onSubmit)}>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Full name" autoComplete="name" error={errorsFor('full_name')} {...register('full_name')} />
            <Field label="Email" type="email" autoComplete="email" error={errorsFor('email')} {...register('email')} />
            <Field label="Phone" type="tel" autoComplete="tel" error={errorsFor('phone')} {...register('phone')} />
            <Field label="City" autoComplete="address-level2" error={errorsFor('city')} {...register('city')} />
          </div>
          <Field label="Street address and area" autoComplete="street-address" error={errorsFor('shipping_address')} {...register('shipping_address')} />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Postal code (optional)" autoComplete="postal-code" error={errorsFor('postal_code')} {...register('postal_code')} />
            <label className="block"><span className="mb-1.5 block text-sm font-medium text-stone-700">Country</span><select className="w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5" {...register('country')}><option value="BD">Bangladesh</option></select></label>
          </div>
          {requestError && <p role="alert" className="rounded-lg bg-rose-50 p-3 text-sm text-rose-800">{requestError}</p>}
          <button disabled={isSubmitting} className="w-full rounded-xl bg-stone-950 px-5 py-3.5 font-semibold text-white hover:bg-stone-700 disabled:opacity-50">{isSubmitting ? 'Placing order…' : `Place COD order · ${formatMoney(total, items[0].currency)}`}</button>
          <p className="text-center text-xs text-stone-500">Cash on delivery · No payment details required</p>
        </form>
      </section>
      <aside className="h-fit rounded-2xl border border-stone-200 bg-white p-5 lg:mt-10"><h2 className="font-semibold">Order summary</h2><div className="mt-4 space-y-3">{items.map((item) => <div key={item.variantId} className="flex justify-between gap-4 text-sm"><span className="text-stone-600">{item.quantity} × {item.productTitle}<span className="block text-xs">{item.variantTitle}</span></span><span className="shrink-0">{formatMoney(item.priceMinor * item.quantity, item.currency)}</span></div>)}</div><div className="mt-5 flex justify-between border-t border-stone-200 pt-4 font-semibold"><span>Total</span><span>{formatMoney(total, items[0].currency)}</span></div><p className="mt-2 text-xs text-stone-500">Shipping included</p></aside>
    </div>
  );
}

export function OrderConfirmationPage() {
  const { storeSlug = '', orderCode = '' } = useParams();
  const location = useLocation();
  const token = new URLSearchParams(location.hash.slice(1)).get('token') ?? '';
  const { data: order, isPending, error } = useQuery({
    queryKey: ['tracked-order', storeSlug, orderCode, token],
    queryFn: () => storeApi.trackOrder(storeSlug, orderCode, token),
    enabled: token.length >= 32,
    retry: false,
  });
  if (!token) return <PageMessage>This tracking link is missing its secure token.</PageMessage>;
  if (isPending) return <PageMessage>Loading your order…</PageMessage>;
  if (error || !order) return <PageMessage>We couldn’t find that order. Check the tracking link and try again.</PageMessage>;
  return (
    <section className="mx-auto max-w-2xl rounded-3xl border border-stone-200 bg-white p-6 sm:p-10">
      <div className="grid h-12 w-12 place-items-center rounded-full bg-lime-100 text-xl text-lime-800">✓</div>
      <p className="mt-5 text-sm font-semibold uppercase tracking-[0.18em] text-stone-500">Order received</p>
      <h1 className="mt-2 font-display text-3xl font-bold">Thank you for your order.</h1>
      <p className="mt-3 text-stone-600">Order <strong>{order.order_code}</strong> is <strong className="capitalize">{order.status}</strong>. Pay cash when it arrives.</p>
      <div className="mt-7 divide-y divide-stone-200 border-y border-stone-200">{order.items.map((item) => <div key={item.sku} className="flex justify-between gap-4 py-4 text-sm"><span>{item.quantity} × {item.product_title}<span className="block text-stone-500">{item.variant_title}</span></span><span>{formatMoney(item.line_total_minor, order.currency)}</span></div>)}</div>
      <div className="mt-5 flex justify-between font-bold"><span>Cash due on delivery</span><span>{formatMoney(order.total_minor, order.currency)}</span></div>
      <p className="mt-5 text-xs leading-5 text-stone-500">Keep this page link to check your order later. Its private link token stays in this browser URL fragment.</p>
      <Link to={`/s/${storeSlug}`} className="mt-6 inline-block rounded-lg bg-stone-950 px-4 py-2.5 text-sm font-semibold text-white">Continue shopping</Link>
    </section>
  );
}

function PageMessage({ children }: { children: ReactNode }) {
  return <div className="rounded-2xl border border-stone-200 bg-white p-8 text-center text-stone-600">{children}</div>;
}
