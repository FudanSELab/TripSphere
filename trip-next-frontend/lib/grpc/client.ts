import * as grpc from "@grpc/grpc-js";

// Attraction
import { AttractionServiceClient } from "@/lib/grpc/gen/tripsphere/attraction/attraction";

// File
import { FileServiceClient } from "@/lib/grpc/gen/tripsphere/file/file";

// Hotel
import { HotelServiceClient } from "@/lib/grpc/gen/tripsphere/hotel/hotel";
import { MetadataServiceClient as HotelMetadataServiceClient } from "@/lib/grpc/gen/tripsphere/hotel/metadata";

// Itinerary
import { MetadataServiceClient as ItineraryMetadataServiceClient } from "@/lib/grpc/gen/tripsphere/itinerary/metadata";

// Note
import { MetadataServiceClient as NoteMetadataServiceClient } from "@/lib/grpc/gen/tripsphere/note/metadata";

// User
import { UserServiceClient } from "@/lib/grpc/gen/tripsphere/user/user";

const AttractionAddress = "127.0.0.1:50053";
const FileAddress = "127.0.0.1:50051";
const HotelAddress = "127.0.0.1:50054";
const ItineraryAddress = "127.0.0.1:50052";
const NoteAddress = "127.0.0.1:50055";
const UserAddress = "127.0.0.1:50056";

export class GrpcClient {
  private static instance: GrpcClient;

  public attraction: AttractionServiceClient;
  public file: FileServiceClient;
  public hotel: HotelServiceClient;
  public hotelMetadata: HotelMetadataServiceClient;
  public itineraryMetadata: ItineraryMetadataServiceClient;
  public noteMetadata: NoteMetadataServiceClient;
  public user: UserServiceClient;

  private constructor(credentials?: grpc.ChannelCredentials) {
    const creds = credentials ?? grpc.credentials.createInsecure();

    this.attraction = new AttractionServiceClient(AttractionAddress, creds);
    this.file = new FileServiceClient(FileAddress, creds);
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
