export type User = {
  id: number;
  phone: string;
  email?: string | null;
  nickname?: string | null;
  role: "user" | "admin";
};

export type Category = { id: number; name: string };

export type Product = {
  id: number;
  categoryId: number;
  categoryName: string;
  name: string;
  spec: string;
  description: string;
  priceCents: number;
  imageUrl: string;
  status: "on" | "off";
  availableQuantity?: number;
  reservedQuantity?: number;
};

export type OrderItem = {
  productId: number;
  productName: string;
  spec: string;
  unitPriceCents: number;
  quantity: number;
};

export type ShopOrder = {
  id: number;
  userId: number;
  status: string;
  totalCents: number;
  traceId: string;
  createdAt: string;
  updatedAt: string;
  items: OrderItem[];
};

export type CartLine = {
  productId: number;
  name: string;
  spec: string;
  priceCents: number;
  imageUrl: string;
  quantity: number;
};
