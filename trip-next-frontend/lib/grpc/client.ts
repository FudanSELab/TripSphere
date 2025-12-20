import * as grpc from "@grpc/grpc-js";

// Attraction
import { AttractionServiceClient } from "./gen/attraction/attraction_grpc_pb";

// Hotel
import { HotelServiceClient } from "./gen/hotel/hotel_grpc_pb";
import { MetadataServiceClient as HotelMetadataServiceClient } from "./gen/hotel/metadata_grpc_pb";

// Itinerary
import { ItineraryPlannerServiceClient } from "./gen/itinerary/itinerary_grpc_pb";
import { MetadataServiceClient as ItineraryMetadataServiceClient } from "./gen/itinerary/metadata_grpc_pb";

// Note
import { MetadataServiceClient as NoteMetadataServiceClient } from "./gen/note/metadata_grpc_pb";

// User
import { UserServiceClient } from "./gen/user/user_grpc_pb";

const AtractionAddress = "127.0.0.1:9007";
const HotelAddress = "127.0.0.1:9007";
const ItineraryAddress = "127.0.0.1:9007";
const NoteAddress = "127.0.0.1:9007";
const UserAddress = "127.0.0.1:9007";

export class GrpcClient {
  private static instance: GrpcClient;

  public attraction: AttractionServiceClient;
  public hotel: HotelServiceClient;
  public hotelMetadata: HotelMetadataServiceClient;
  public itineraryPlanner: ItineraryPlannerServiceClient;
  public itineraryMetadata: ItineraryMetadataServiceClient;
  public noteMetadata: NoteMetadataServiceClient;
  public user: UserServiceClient;

  private constructor(credentials?: grpc.ChannelCredentials) {
    const creds = credentials ?? grpc.credentials.createInsecure();

    this.attraction = new AttractionServiceClient(AtractionAddress, creds);
    this.hotel = new HotelServiceClient(HotelAddress, creds);
    this.hotelMetadata = new HotelMetadataServiceClient(HotelAddress, creds);
    this.itineraryPlanner = new ItineraryPlannerServiceClient(ItineraryAddress, creds);
    this.itineraryMetadata = new ItineraryMetadataServiceClient(ItineraryAddress, creds);
    this.noteMetadata = new NoteMetadataServiceClient(NoteAddress, creds);
    this.user = new UserServiceClient(UserAddress, creds);
  }

  public static getInstance(
    credentials?: grpc.ChannelCredentials
  ): GrpcClient {
    if (!GrpcClient.instance) {
      GrpcClient.instance = new GrpcClient(credentials);
    }
    return GrpcClient.instance;
  }
}

export const grpcClient = GrpcClient.getInstance();

