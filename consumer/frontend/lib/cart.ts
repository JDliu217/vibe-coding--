import { CartLine } from "./types";

function storageKey() {
  const userId = localStorage.getItem("freshmart-user-id") || "guest";
  return `freshmart-cart:${userId}`;
}

export function readCart(): CartLine[] {
  try {
    return JSON.parse(localStorage.getItem(storageKey()) || "[]");
  } catch {
    return [];
  }
}

export function writeCart(lines: CartLine[]) {
  localStorage.setItem(storageKey(), JSON.stringify(lines));
  window.dispatchEvent(new Event("freshmart-cart"));
}

export function addToCart(line: Omit<CartLine, "quantity">, quantity: number) {
  const lines = readCart();
  const found = lines.find((item) => item.productId === line.productId);
  if (found) found.quantity = Math.min(99, found.quantity + quantity);
  else lines.push({ ...line, quantity });
  writeCart(lines);
}

export function cartCount() {
  return readCart().reduce((sum, line) => sum + line.quantity, 0);
}
