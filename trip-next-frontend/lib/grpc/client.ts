import * as grpc from "@grpc/grpc-js";

// Attraction
import { AttractionServiceClient } from "@/lib/grpc/gen/tripsphere/attraction/attraction";

// Hotel
import { HotelServiceClient } from "@/lib/grpc/gen/tripsphere/hotel/hotel";
import { MetadataServiceClient as HotelMetadataServiceClient } from "@/lib/grpc/gen/tripsphere/hotel/metadata";

// Itinerary
import { MetadataServiceClient as ItineraryMetadataServiceClient } from "@/lib/grpc/gen/tripsphere/itinerary/metadata";

// Note
import { MetadataServiceClient as NoteMetadataServiceClient } from "@/lib/grpc/gen/tripsphere/note/metadata";

// User
import { UserServiceClient } from "@/lib/grpc/gen/tripsphere/user/user";

const AtractionAddress = "127.0.0.1:9006";
const HotelAddress = "127.0.0.1:9010";
const ItineraryAddress = "127.0.0.1:50052";
const NoteAddress = "127.0.0.1:9090";
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
