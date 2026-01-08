import * as grpc from "@grpc/grpc-js";

// Attraction
import { AttractionServiceClient } from "@/lib/grpc/gen/attraction/attraction_grpc_pb";

// Hotel
import { HotelServiceClient } from "@/lib/grpc/gen/hotel/hotel_grpc_pb";
import { MetadataServiceClient as HotelMetadataServiceClient } from "@/lib/grpc/gen/hotel/metadata_grpc_pb";

// Itinerary
import { MetadataServiceClient as ItineraryMetadataServiceClient } from "@/lib/grpc/gen/itinerary/metadata_grpc_pb";

// Note
import { MetadataServiceClient as NoteMetadataServiceClient } from "@/lib/grpc/gen/note/metadata_grpc_pb";

// User
import { UserServiceClient } from "@/lib/grpc/gen/user/user_grpc_pb";

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
  public itineraryMetadata: ItineraryMetadataServiceClient;
  public noteMetadata: NoteMetadataServiceClient;
  public user: UserServiceClient;

  private constructor(credentials?: grpc.ChannelCredentials) {
    const creds = credentials ?? grpc.credentials.createInsecure();

    this.attraction = new AttractionServiceClient(AtractionAddress, creds);
    this.hotel = new HotelServiceClient(HotelAddress, creds);
    this.hotelMetadata = new HotelMetadataServiceClient(HotelAddress, creds);
    this.itineraryMetadata = new ItineraryMetadataServiceClient(
      ItineraryAddress,
      creds,
    );
    this.noteMetadata = new NoteMetadataServiceClient(NoteAddress, creds);
    this.user = new UserServiceClient(UserAddress, creds);
  }

  public static getInstance(credentials?: grpc.ChannelCredentials): GrpcClient {
    if (!GrpcClient.instance) {
      GrpcClient.instance = new GrpcClient(credentials);
    }
    return GrpcClient.instance;
  }
}

export const grpcClient = GrpcClient.getInstance();
