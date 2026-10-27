const shops: Record<string, { image: string; products: string[] }> = {
  'bay-leaf-pantry': { image: '/demo-images/bay-leaf-pantry.jpg', products: ['Sylhet Seven Spice', 'Green Mango Achar', 'Cold-Pressed Mustard Oil', 'Tea Garden Masala Chai'] },
  'loom-and-lilt': { image: '/demo-images/loom-and-lilt.jpg', products: ['Soft Muslin Wrap', 'Jamdani Everyday Tote', 'Kantha Weekend Throw', 'Indigo Cotton Scarf'] },
  'clay-and-kin': { image: '/demo-images/clay-and-kin.jpg', products: ['Riverstone Coffee Cup', 'Sunday Breakfast Bowl', 'Little Wildflower Vase', 'Soft Dawn Incense Dish'] },
  'paper-trail-studio': { image: '/demo-images/paper-trail-studio.jpg', products: ['Forest Block-Print Journal', 'Quiet Correspondence Set', 'Recycled Gift Wrap', 'Wildflower Note Cards'] },
  'orchard-and-bloom': { image: '/demo-images/orchard-and-bloom.jpg', products: ['Sunroom Mini Bouquet', 'Meadow-Dried Flowers', 'Balcony Herb Planter', 'Pollinator Seed Kit'] },
  'lightwell-home': { image: '/demo-images/lightwell-home.jpg', products: ['Amber Hour Candle', 'Cloud Linen Cushion Cover', 'Brass Dew Incense Holder', 'Woven Everyday Runner'] },
};

export function demoShopImage(slug: string): string | null {
  return shops[slug]?.image ?? null;
}

export function demoProductPhoto(slug: string, title: string): { image: string; tile: number } | null {
  const shop = shops[slug];
  const tile = shop?.products.indexOf(title) ?? -1;
  return shop && tile >= 0 ? { image: shop.image, tile } : null;
}
