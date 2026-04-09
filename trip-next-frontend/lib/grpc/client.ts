import "server-only";

import { credentials, Metadata, type ChannelCredentials } from "@grpc/grpc-js";
import { headers } from "next/headers";
import { config } from "@/lib/env";
import { UserServiceClient } from "./generated/tripsphere/user/v1/user";
import { HotelServiceClient } from "./generated/tripsphere/hotel/v1/hotel";
import { AttractionServiceClient } from "./generated/tripsphere/attraction/v1/attraction";
import { ItineraryServiceClient } from "./generated/tripsphere/itinerary/v1/itinerary";
import { PoiServiceClient } from "./generated/tripsphere/poi/v1/poi";
import { OrderServiceClient } from "./generated/tripsphere/order/v1/order";
import { ProductServiceClient } from "./generated/tripsphere/product/v1/product";

const clientCache = new Map<string, unknown>();

function getGrpcClient<T>(
  ClientConstructor: new (
    address: string,
    credentials: ChannelCredentials,
  ) => T,
  address: string,
): T {
  const key = `${ClientConstructor.name}@${address}`;
  if (!clientCache.has(key)) {
    clientCache.set(
      key,
      new ClientConstructor(address, credentials.createInsecure()),
    );
  }
  return clientCache.get(key) as T;
}

export function getUserService() {
  return getGrpcClient(UserServiceClient, config.grpc.userService);
}

export function getHotelService() {
  return getGrpcClient(HotelServiceClient, config.grpc.hotelService);
}

export function getAttractionService() {
  return getGrpcClient(AttractionServiceClient, config.grpc.attractionService);
}

export function getItineraryService() {
  return getGrpcClient(ItineraryServiceClient, config.grpc.itineraryService);
}

export function getPoiService() {
  return getGrpcClient(PoiServiceClient, config.grpc.poiService);
}

export function getProductService() {
  return getGrpcClient(ProductServiceClient, config.grpc.productService);
}

export function getOrderService() {
  return getGrpcClient(OrderServiceClient, config.grpc.orderService);
}

export async function getAuthMetadata(): Promise<Metadata> {
  const metadata = new Metadata();
  const reqHeaders = await headers();
  const authorization = reqHeaders.get("authorization");
  const userId = reqHeaders.get("x-user-id");
  const userRoles = reqHeaders.get("x-user-roles");
  if (authorization) metadata.set("authorization", authorization);
  if (userId) metadata.set("x-user-id", userId);
  if (userRoles) metadata.set("x-user-roles", userRoles);
  return metadata;
}
