import "server-only";
import { credentials, Metadata, type ChannelCredentials } from "@grpc/grpc-js";
import { headers } from "next/headers";
import { UserServiceClient } from "./generated/tripsphere/user/v1/user";
import { HotelServiceClient } from "./generated/tripsphere/hotel/v1/hotel";
import { AttractionServiceClient } from "./generated/tripsphere/attraction/v1/attraction";
import { ItineraryServiceClient } from "./generated/tripsphere/itinerary/v1/itinerary";
import { PoiServiceClient } from "./generated/tripsphere/poi/v1/poi";
import { ProductServiceClient } from "./generated/tripsphere/product/v1/product";

// Static service addresses
const SERVICE_ADDRESSES = {
  "trip-attraction-service": "localhost:50053",
  "trip-hotel-service": "localhost:50054",
  "trip-inventory-service": "localhost:50061",
  "trip-itinerary-service": "localhost:50052",
  "trip-poi-service": "localhost:50058",
  "trip-product-service": "localhost:50060",
  "trip-user-service": "localhost:50056",
};

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
  return getGrpcClient(
    UserServiceClient,
    SERVICE_ADDRESSES["trip-user-service"],
  );
}

export function getHotelService() {
  return getGrpcClient(
    HotelServiceClient,
    SERVICE_ADDRESSES["trip-hotel-service"],
  );
}

export function getAttractionService() {
  return getGrpcClient(
    AttractionServiceClient,
    SERVICE_ADDRESSES["trip-attraction-service"],
  );
}

export function getItineraryService() {
  return getGrpcClient(
    ItineraryServiceClient,
    SERVICE_ADDRESSES["trip-itinerary-service"],
  );
}

export function getPoiService() {
  return getGrpcClient(PoiServiceClient, SERVICE_ADDRESSES["trip-poi-service"]);
}

export function getProductService() {
  return getGrpcClient(
    ProductServiceClient,
    SERVICE_ADDRESSES["trip-product-service"],
  );
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
