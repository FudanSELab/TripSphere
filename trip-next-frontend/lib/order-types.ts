export const ORDER_STATUS_PENDING_PAYMENT = 1;
export const ORDER_STATUS_PAID = 2;
export const ORDER_STATUS_COMPLETED = 3;
export const ORDER_STATUS_CANCELLED = 4;

export const ORDER_TYPE_ATTRACTION = 1;
export const ORDER_TYPE_HOTEL = 2;
export const ORDER_TYPE_FLIGHT = 3;
export const ORDER_TYPE_TRAIN = 4;

export interface OrderItemData {
  id: string;
  spuName: string;
  skuName: string;
  date?: { year: number; month: number; day: number };
  endDate?: { year: number; month: number; day: number };
  quantity: number;
  unitPrice?: { currency: string; units: number; nanos: number };
  subtotal?: { currency: string; units: number; nanos: number };
  spuImage: string;
  spuDescription: string;
  resourceId: string;
}

export interface OrderData {
  id: string;
  orderNo: string;
  status: number;
  type: number;
  items: OrderItemData[];
  contact?: { name: string; phone: string; email: string };
  totalAmount?: { currency: string; units: number; nanos: number };
  createdAt?: string;
  resourceId: string;
}
