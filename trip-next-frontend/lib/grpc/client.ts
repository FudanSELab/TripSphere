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

// Review
import { ReviewServiceClient } from "@/lib/grpc/gen/tripsphere/review/review";

// User
import { UserServiceClient } from "@/lib/grpc/gen/tripsphere/user/user";

// Use environment variables with Docker service names as defaults
const AttractionAddress =
  process.env.GRPC_ATTRACTION_ADDRESS || "trip-attraction-service:50053";
const FileAddress = process.env.GRPC_FILE_ADDRESS || "trip-file-service:50051";
const HotelAddress =
  process.env.GRPC_HOTEL_ADDRESS || "trip-hotel-service:50054";
const ItineraryAddress =
  process.env.GRPC_ITINERARY_ADDRESS || "trip-itinerary-service:50052";
const NoteAddress = process.env.GRPC_NOTE_ADDRESS || "trip-note-service:50055";
const ReviewAddress =
  process.env.GRPC_REVIEW_ADDRESS || "trip-review-service:50057";
const UserAddress = process.env.GRPC_USER_ADDRESS || "trip-user-service:50056";

export class GrpcClient {
  private static instance: GrpcClient;

  public attraction: AttractionServiceClient;
  public file: FileServiceClient;
  public hotel: HotelServiceClient;
  public hotelMetadata: HotelMetadataServiceClient;
  public itineraryMetadata: ItineraryMetadataServiceClient;
  public noteMetadata: NoteMetadataServiceClient;
  public review: ReviewServiceClient;
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
    this.review = new ReviewServiceClient(ReviewAddress, creds);
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
