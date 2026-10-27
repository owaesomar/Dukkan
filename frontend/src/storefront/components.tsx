import { Link, useParams } from 'react-router-dom';
import type { StoreProduct, StoreVariant } from '../lib/api';
import { useCart } from './cart';
import { demoProductPhoto } from './demo-art';

export function formatMoney(amountMinor: number, currency: string) {
  const formatter = new Intl.NumberFormat(undefined, { style: 'currency', currency });
  const fractionDigits = formatter.resolvedOptions().maximumFractionDigits ?? 2;
  return formatter.format(amountMinor / 10 ** fractionDigits);
}

export function StoreHeader({ storeName }: { storeName: string }) {
  const { storeSlug = '' } = useParams();
  const count = useCart((state) =>
    state.storeSlug === storeSlug ? state.items.reduce((total, item) => total + item.quantity, 0) : 0,
  );
  return (
    <header className="border-b border-stone-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
        <Link className="font-display text-xl font-bold tracking-tight" to={`/s/${storeSlug}`}>
          {storeName}
        </Link>
        <nav className="flex items-center gap-5 text-sm font-medium">
          <Link className="hidden text-stone-600 hover:text-stone-950 sm:inline" to="/shops">All shops</Link>
          <Link className="text-stone-600 hover:text-stone-950" to={`/s/${storeSlug}`}>
            Shop
          </Link>
          <Link className="rounded-full bg-stone-950 px-4 py-2 text-white hover:bg-stone-700" to={`/s/${storeSlug}/cart`}>
            Bag <span className="ml-1 text-stone-300">{count}</span>
          </Link>
        </nav>
      </div>
    </header>
  );
}

export function ProductArtwork({ title, categoryId, storeSlug, compact = false }: { title: string; categoryId: number | null; storeSlug?: string; compact?: boolean }) {
  const demoPhoto = storeSlug ? demoProductPhoto(storeSlug, title) : null;
  if (demoPhoto) {
    const positions = ['0% 0%', '100% 0%', '0% 100%', '100% 100%'];
    return <div role="img" aria-label={title} className="h-full w-full" style={{ backgroundImage: `url(${demoPhoto.image})`, backgroundPosition: positions[demoPhoto.tile], backgroundSize: '200% 200%' }} />;
  }
  const palettes = [
    'from-amber-100 via-orange-50 to-rose-200 text-orange-900',
    'from-emerald-100 via-lime-50 to-teal-200 text-emerald-900',
    'from-sky-100 via-blue-50 to-indigo-200 text-blue-900',
    'from-violet-100 via-fuchsia-50 to-rose-200 text-violet-900',
  ];
  const palette = palettes[(categoryId ?? title.length) % palettes.length];
  return (
    <div aria-hidden="true" className={`relative grid h-full w-full place-items-center overflow-hidden bg-gradient-to-br ${palette}`}>
      <span className="absolute -right-[12%] -top-[25%] h-[65%] w-[65%] rounded-full bg-white/35" />
      <span className="absolute -bottom-[28%] -left-[13%] h-[72%] w-[72%] rounded-full border-[20px] border-white/30" />
      <span className={`relative grid place-items-center rounded-[30%] border border-white/70 bg-white/45 font-display font-bold shadow-sm backdrop-blur-sm ${compact ? 'h-16 w-16 text-2xl' : 'h-24 w-24 text-4xl'}`}>{title.trim().charAt(0).toUpperCase()}</span>
    </div>
  );
}

export function ProductCard({ storeSlug, product }: { storeSlug: string; product: StoreProduct }) {
  const add = useCart((state) => state.add);
  const variant = product.variants.find((item) => item.available_quantity > 0);
  const image = product.media[0];
  return (
    <article className="group overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
      <Link to={`/s/${storeSlug}/products/${product.id}`} className="block">
        <div className="aspect-[4/3] overflow-hidden bg-stone-100">
          {image?.image_url ? (
            <img className="h-full w-full object-cover transition duration-500 group-hover:scale-105" src={image.image_url} alt={image.alt_text || product.title} />
          ) : <ProductArtwork title={product.title} categoryId={product.category_id} storeSlug={storeSlug} />}
        </div>
        <div className="p-4">
          <h2 className="font-semibold">{product.title}</h2>
          <p className="mt-1 text-sm text-stone-500">
            {variant ? formatMoney(variant.price_minor, variant.currency) : 'Unavailable'}
          </p>
        </div>
      </Link>
      <div className="px-4 pb-4">
        <button
          className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm font-semibold transition hover:border-stone-950 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={!variant}
          onClick={() => variant && add(storeSlug, cartItem(product, variant))}
        >
          {variant ? 'Add to bag' : 'Sold out'}
        </button>
      </div>
    </article>
  );
}

export function cartItem(product: StoreProduct, variant: StoreVariant) {
  return {
    productId: product.id,
    variantId: variant.id,
    productTitle: product.title,
    variantTitle: variant.title,
    sku: variant.sku,
    priceMinor: variant.price_minor,
    currency: variant.currency,
    imageUrl: product.media[0]?.image_url ?? null,
  };
}
