"use client";

import { ReviewForm } from "@/components/reviews/review-form";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAttractions } from "@/hooks/use-attractions";
import { useChatSidebar } from "@/hooks/use-chat-sidebar";
import type { Attraction, ChatContext, Review } from "@/lib/types";
import {
  ChevronLeft,
  Clock,
  Cloud,
  Heart,
  MapPin,
  MessageCircle,
  Share2,
  Star,
  Ticket,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

export default function AttractionDetailPage() {
  const params = useParams();
  const attractionId = params.id as string;
  const { fetchAttraction } = useAttractions();
  const chatSidebar = useChatSidebar();

  // TODO: Replace with real authentication when user service is integrated
  const currentUser = { id: "user-1", username: "Demo User" };

  // State
  const [attraction, setAttraction] = useState<Attraction | null>(null);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [userReview, setUserReview] = useState<Review | null>(null);

  // Scroll to top when navigating to this page
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Fetch attraction data
  useEffect(() => {
    const loadAttraction = async () => {
      try {
        const data = await fetchAttraction(attractionId);
        setAttraction(data);
      } catch (error) {
        console.error("Error loading attraction:", error);
      }
    };

    loadAttraction();
  }, [attractionId]);

  // Fetch reviews
  const fetchReviews = async () => {
    setReviewsLoading(true);
    try {
      // This would call the actual API
      // const response = await fetch(`${process.env.NEXT_PUBLIC_REVIEW_SERVICE_URL}/reviews?targetType=attraction&targetId=${attractionId}`)
      // For now, using mock data
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Mock reviews data
      const mockReviews: Review[] = [
        {
          id: "review-1",
          userId: "user-2",
          targetType: "attraction",
          targetId: attractionId,
          rating: 5,
          text: "Absolutely stunning views, especially at night! The historic buildings are beautifully preserved and the modern skyline across the river is breathtaking.",
          images: [
            "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=400&h=300&fit=crop",
          ],
          createdAt: Date.now() - 86400000 * 2,
          updatedAt: Date.now() - 86400000 * 2,
        },
        {
          id: "review-2",
          userId: "user-3",
          targetType: "attraction",
          targetId: attractionId,
          rating: 4,
          text: "Great place for a walk along the waterfront. Very crowded during weekends and holidays though.",
          images: [],
          createdAt: Date.now() - 86400000 * 5,
          updatedAt: Date.now() - 86400000 * 5,
        },
        {
          id: "review-3",
          userId: "user-4",
          targetType: "attraction",
          targetId: attractionId,
          rating: 5,
          text: "Perfect spot for photography! Visited during sunset and the golden hour lighting was amazing.",
          images: [
            "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=400&h=300&fit=crop",
            "https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=400&h=300&fit=crop",
          ],
          createdAt: Date.now() - 86400000 * 7,
          updatedAt: Date.now() - 86400000 * 7,
        },
      ];

      setReviews(mockReviews);

      // Check if current user has reviewed
      setUserReview(
        mockReviews.find((r) => r.userId === currentUser.id) || null,
      );
    } finally {
      setReviewsLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, [attractionId]);

  const handleReviewSubmit = () => {
    setShowReviewForm(false);
    fetchReviews();
  };

  const handleReviewEdit = () => {
    setShowReviewForm(true);
  };

  const openReviewForm = () => {
    setShowReviewForm(true);
  };

  const closeReviewForm = () => {
    setShowReviewForm(false);
  };

  const handleReviewDelete = async () => {
    if (confirm("Are you sure you want to delete your review?")) {
      // Call delete API
      setUserReview(null);
      fetchReviews();
    }
  };

  const handleAskAboutReviews = () => {
    // Open chat sidebar with review context, routing to review_summary A2A agent
    if (attraction) {
      const context: ChatContext = {
        // Frontend UI fields
        type: "review-summary",
        displayName: attraction.name,
        // Backend metadata fields (sent to trip-chat-service)
        agent: "review_summary",
        target_id: attractionId,
        target_type: "attraction",
      };
      chatSidebar.open(context, `Reviews for ${attraction.name}`);
    }
  };

  const handleWeatherAndTips = () => {
    if (!attraction) return;

    // Prepare the query template with attraction info
    const query = `Please help me check the weather conditions and travel tips for ${attraction.name} located in ${attraction.address.city}, ${attraction.address.country}.`;

    const context: ChatContext = {
      // Frontend UI fields
      type: "attraction",
      displayName: attraction.name,
      autoSendQuery: query,
      // Backend metadata fields (sent to trip-chat-service)
      agent: "journey_assistant",
      target_id: attractionId,
      target_type: "attraction",
    };
    chatSidebar.open(context, `Weather & Tips: ${attraction.name}`);
  };

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const getRatingStars = (rating: number) => {
    return Array(5)
      .fill(0)
      .map((_, i) => i < rating);
  };

  if (!attraction) {
    return null;
  }

  return (
    <div className="bg-muted min-h-screen">
      {/* Back button */}
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
        <Link
          href="/attractions"
          className="text-muted-foreground hover:text-foreground inline-flex items-center gap-2 transition-colors"
        >
          <ChevronLeft className="h-5 w-5" />
          Back to Attractions
        </Link>
      </div>

      {/* Main content */}
      <div className="mx-auto max-w-7xl px-4 pb-8 sm:px-6 lg:px-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left column - Main content */}
          <div className="space-y-6 lg:col-span-2">
            {/* Image gallery */}
            <div className="bg-background overflow-hidden rounded-xl shadow-sm">
              <div className="relative aspect-video">
                <img
                  src={attraction.images?.[selectedImageIndex]}
                  alt={attraction.name}
                  className="h-full w-full object-cover"
                />
              </div>
              {attraction.images && attraction.images.length > 1 && (
                <div className="p-4">
                  <div className="flex gap-2 overflow-x-auto">
                    {attraction.images.map((image, index) => (
                      <button
                        key={index}
                        className={`h-20 w-20 shrink-0 overflow-hidden rounded-lg border-2 transition-all ${
                          selectedImageIndex === index
                            ? "border-primary ring-primary/20 ring-2"
                            : "border-border hover:border-border/80"
                        }`}
                        onClick={() => setSelectedImageIndex(index)}
                      >
                        <img
                          src={image}
                          alt={`${attraction.name} - Image ${index + 1}`}
                          className="h-full w-full object-cover"
                        />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Basic info */}
            <div className="bg-background rounded-xl p-6 shadow-sm">
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <div className="mb-2 flex items-center gap-2">
                    <Badge variant="default">{attraction.category}</Badge>
                    {attraction.tags && (
                      <div className="flex gap-2">
                        {attraction.tags.slice(0, 3).map((tag, index) => (
                          <Badge
                            key={`${attraction.id}-tag-${index}`}
                            variant="secondary"
                          >
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <h1 className="text-foreground mb-2 text-3xl font-bold">
                    {attraction.name}
                  </h1>
                  <div className="text-muted-foreground flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {attraction.address.city}, {attraction.address.country}
                    </div>
                    {attraction.rating && (
                      <div className="text-chart-4 flex items-center gap-1">
                        <Star className="h-4 w-4 fill-current" />
                        <span className="text-foreground font-medium">
                          {attraction.rating}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    className="bg-muted text-muted-foreground hover:bg-muted/80 flex h-10 w-10 items-center justify-center rounded-full transition-colors"
                    title="Share"
                  >
                    <Share2 className="h-5 w-5" />
                  </button>
                  <button
                    className="bg-muted text-muted-foreground hover:bg-destructive/10 hover:text-destructive flex h-10 w-10 items-center justify-center rounded-full transition-colors"
                    title="Add to favorites"
                  >
                    <Heart className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="border-border border-t pt-4">
                <h2 className="text-foreground mb-3 text-lg font-semibold">
                  About
                </h2>
                <p className="text-muted-foreground leading-relaxed">
                  {attraction.description}
                </p>
              </div>

              <div className="border-border mt-6 border-t pt-6">
                <h2 className="text-foreground mb-4 text-lg font-semibold">
                  Address
                </h2>
                <p className="text-muted-foreground">
                  {attraction.address.street}
                  <br />
                  {attraction.address.county}, {attraction.address.city}
                  <br />
                  {attraction.address.province}, {attraction.address.country}
                </p>
              </div>
            </div>

            {/* Reviews Section */}
            <div
              id="reviews"
              className="bg-background rounded-xl p-6 shadow-sm"
            >
              <div className="mb-6 flex items-center justify-between">
                <h2 className="text-foreground text-2xl font-bold">Reviews</h2>
                <div className="flex gap-3">
                  <Button variant="outline" onClick={handleAskAboutReviews}>
                    <MessageCircle className="mr-2 h-4 w-4" />
                    Ask About Reviews
                  </Button>
                  {!userReview && (
                    <Button variant="default" onClick={openReviewForm}>
                      Write a Review
                    </Button>
                  )}
                </div>
              </div>

              {/* Review Form */}
              {showReviewForm && (
                <div className="mb-6">
                  <ReviewForm
                    attractionId={attractionId}
                    userId={currentUser.id}
                    existingReview={userReview}
                    onSubmit={handleReviewSubmit}
                    onCancel={closeReviewForm}
                  />
                </div>
              )}

              {/* User's own review (shown at top) */}
              {userReview && !showReviewForm && (
                <div className="mb-6">
                  <div className="border-primary/20 bg-primary/5 rounded-lg border p-4">
                    <div className="mb-3 flex items-start justify-between">
                      <div>
                        <div className="mb-1 flex items-center gap-2">
                          <span className="text-foreground font-semibold">
                            Your Review
                          </span>
                          <div className="flex gap-0.5">
                            {getRatingStars(userReview.rating).map(
                              (filled, index) => (
                                <Star
                                  key={index}
                                  className={`h-4 w-4 ${filled ? "text-chart-4 fill-current" : "text-muted-foreground/30"}`}
                                />
                              ),
                            )}
                          </div>
                        </div>
                        <p className="text-muted-foreground text-sm">
                          {formatDate(userReview.createdAt)}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleReviewEdit}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={handleReviewDelete}
                        >
                          Delete
                        </Button>
                      </div>
                    </div>
                    <p className="text-foreground mb-3">{userReview.text}</p>
                    {userReview.images.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {userReview.images.map((image, index) => (
                          <img
                            key={index}
                            src={image}
                            alt={`Review image ${index + 1}`}
                            className="h-24 w-24 rounded-lg object-cover"
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Other reviews */}
              {reviewsLoading ? (
                <div className="py-8 text-center">
                  <p className="text-muted-foreground">Loading reviews...</p>
                </div>
              ) : reviews.length === 0 ? (
                <div className="py-8 text-center">
                  <p className="text-muted-foreground">
                    No reviews yet. Be the first to review!
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {reviews
                    .filter((r) => r.userId !== currentUser.id)
                    .map((review) => (
                      <div
                        key={review.id}
                        className="border-border border-b pb-6 last:border-0"
                      >
                        <div className="flex items-start gap-4">
                          <div className="bg-muted flex h-10 w-10 items-center justify-center rounded-full">
                            <span className="text-muted-foreground text-sm font-medium">
                              U
                            </span>
                          </div>
                          <div className="flex-1">
                            <div className="mb-1 flex items-center gap-2">
                              <span className="text-foreground font-semibold">
                                User {review.userId.slice(-1)}
                              </span>
                              <div className="flex gap-0.5">
                                {getRatingStars(review.rating).map(
                                  (filled, index) => (
                                    <Star
                                      key={index}
                                      className={`h-4 w-4 ${filled ? "text-chart-4 fill-current" : "text-muted-foreground/30"}`}
                                    />
                                  ),
                                )}
                              </div>
                            </div>
                            <p className="text-muted-foreground mb-3 text-sm">
                              {formatDate(review.createdAt)}
                            </p>
                            <p className="text-foreground mb-3">
                              {review.text}
                            </p>
                            {review.images.length > 0 && (
                              <div className="flex flex-wrap gap-2">
                                {review.images.map((image, index) => (
                                  <img
                                    key={index}
                                    src={image}
                                    alt={`Review image ${index + 1}`}
                                    className="h-24 w-24 rounded-lg object-cover"
                                  />
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>

          {/* Right column - Sidebar info */}
          <div className="lg:col-span-1">
            <div className="bg-background sticky top-22 rounded-xl p-6 shadow-sm">
              <h3 className="text-foreground mb-4 text-lg font-semibold">
                Visit Information
              </h3>

              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Clock className="text-muted-foreground mt-0.5 h-5 w-5" />
                  <div>
                    <p className="text-foreground font-medium">Opening Hours</p>
                    <p className="text-muted-foreground text-sm">
                      {attraction.openingHours}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Ticket className="text-muted-foreground mt-0.5 h-5 w-5" />
                  <div>
                    <p className="text-foreground font-medium">Ticket Price</p>
                    <p className="text-muted-foreground text-sm">
                      {attraction.ticketPrice}
                    </p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <MapPin className="text-muted-foreground mt-0.5 h-5 w-5" />
                  <div>
                    <p className="text-foreground font-medium">Location</p>
                    <p className="text-muted-foreground text-sm">
                      {attraction.location.lat.toFixed(4)},{" "}
                      {attraction.location.lng.toFixed(4)}
                    </p>
                  </div>
                </div>

                <div
                  onClick={handleWeatherAndTips}
                  className="hover:bg-muted -mx-3 flex cursor-pointer items-start gap-3 rounded-lg px-3 py-2 transition-colors"
                >
                  <Cloud className="text-muted-foreground mt-0.5 h-5 w-5" />
                  <div>
                    <p className="text-foreground font-medium">
                      Weather & Tips
                    </p>
                    <p className="text-muted-foreground text-sm">
                      Check weather and travel tips
                    </p>
                  </div>
                </div>
              </div>

              <div className="border-border mt-6 border-t pt-6">
                <Button variant="default" className="w-full">
                  Get Directions
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
