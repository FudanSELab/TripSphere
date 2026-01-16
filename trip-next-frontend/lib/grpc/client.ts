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
const AttractionUrl =
  process.env.GRPC_ATTRACTION_URL || "trip-attraction-service:50053";
const FileUrl = process.env.GRPC_FILE_URL || "trip-file-service:50051";
const HotelUrl = process.env.GRPC_HOTEL_URL || "trip-hotel-service:50054";
const ItineraryUrl =
  process.env.GRPC_ITINERARY_URL || "trip-itinerary-service:50052";
const NoteUrl = process.env.GRPC_NOTE_URL || "trip-note-service:50055";
const ReviewUrl = process.env.GRPC_REVIEW_URL || "trip-review-service:50057";
const UserUrl = process.env.GRPC_USER_URL || "trip-user-service:50056";

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

    this.attraction = new AttractionServiceClient(AttractionUrl, creds);
    this.file = new FileServiceClient(FileUrl, creds);
    this.hotel = new HotelServiceClient(HotelUrl, creds);
    this.hotelMetadata = new HotelMetadataServiceClient(HotelUrl, creds);
    this.itineraryMetadata = new ItineraryMetadataServiceClient(
      ItineraryUrl,
      creds,
    );
    this.noteMetadata = new NoteMetadataServiceClient(NoteUrl, creds);
    this.review = new ReviewServiceClient(ReviewUrl, creds);
    this.user = new UserServiceClient(UserUrl, creds);
  }

  public static getInstance(credentials?: grpc.ChannelCredentials): GrpcClient {
    if (!GrpcClient.instance) {
      GrpcClient.instance = new GrpcClient(credentials);
    }
    return GrpcClient.instance;
  }
}

export const grpcClient = GrpcClient.getInstance();
