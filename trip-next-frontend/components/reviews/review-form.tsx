"use client";

import { Button } from "@/components/ui/button";
import { useReviews } from "@/lib/hooks/use-reviews";
import type { Review } from "@/lib/types";
import { Star, Upload, X } from "lucide-react";
import { useState } from "react";

interface ReviewFormProps {
  attractionId: string;
  existingReview?: Review | null;
  userId?: string; // TODO: Make this required when user authentication is implemented
  onSubmit: () => void;
  onCancel: () => void;
}

export function ReviewForm({
  attractionId,
  existingReview = null,
  userId = "user-1", // Default mock user ID - TODO: Remove when authentication is added
  onSubmit,
  onCancel,
}: ReviewFormProps) {
  const { createReview: createReviewAPI, updateReview: updateReviewAPI } =
    useReviews();
  const [rating, setRating] = useState(existingReview?.rating || 0);
  const [text, setText] = useState(existingReview?.text || "");
  const [images, setImages] = useState<string[]>(existingReview?.images || []);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const MAX_IMAGES = 10;
  const MAX_TEXT_LENGTH = 2000;

  const handleImageUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Please upload an image file");
      return;
    }

    if (images.length >= MAX_IMAGES) {
      setError(`Maximum ${MAX_IMAGES} images allowed`);
      return;
    }

    // In production, upload to file service and get URL
    // For now, create a local preview URL
    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target?.result) {
        setImages([...images, e.target.result as string]);
      }
    };
    reader.readAsDataURL(file);

    // Reset input
    event.target.value = "";
  };

  const removeImage = (index: number) => {
    setImages(images.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    // Validation
    if (rating === 0) {
      setError("Please select a rating");
      return;
    }

    if (!text.trim()) {
      setError("Please write a review");
      return;
    }

    if (text.length > MAX_TEXT_LENGTH) {
      setError(`Review text must be less than ${MAX_TEXT_LENGTH} characters`);
      return;
    }

    setError("");
    setIsSubmitting(true);

    try {
      if (existingReview) {
        // Update existing review
        const result = await updateReviewAPI({
          id: existingReview.id,
          rating: rating,
          text: text,
          images: images,
        });

        if (!result.status) {
          throw new Error("Failed to update review");
        }
      } else {
        // Create new review
        const result = await createReviewAPI({
          userId: userId,
          targetType: "attraction",
          targetId: attractionId,
          rating: rating,
          text: text,
          images: images,
        });

        if (!result.status) {
          throw new Error("Failed to create review");
        }
      }

      onSubmit();
    } catch (err) {
      setError("Failed to submit review. Please try again.");
      console.error("Error submitting review:", err);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper to check if star is filled
  const isStarFilled = (index: number) => {
    return rating >= index + 1;
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50 p-6">
      <h3 className="mb-4 text-lg font-semibold text-gray-900">
        {existingReview ? "Edit Your Review" : "Write a Review"}
      </h3>

      {/* Error message */}
      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-600">
          {error}
        </div>
      )}

      {/* Rating */}
      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Rating <span className="text-red-500">*</span>
        </label>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((i) => (
            <button
              key={i}
              type="button"
              className={`transition-colors ${
                isStarFilled(i - 1)
                  ? "text-amber-400"
                  : "text-gray-300 hover:text-amber-300"
              }`}
              onClick={() => setRating(i)}
            >
              <Star
                className={`h-8 w-8 ${isStarFilled(i - 1) ? "fill-current" : ""}`}
              />
            </button>
          ))}
        </div>
        <p className="mt-1 text-xs text-gray-500">
          {rating === 0
            ? "Select a rating"
            : rating <= 2
              ? `${rating} star${rating > 1 ? "s" : ""} - Poor`
              : rating === 3
                ? "3 stars - Average"
                : rating === 4
                  ? "4 stars - Good"
                  : "5 stars - Excellent"}
        </p>
      </div>

      {/* Text content */}
      <div className="mb-4">
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Your Review <span className="text-red-500">*</span>
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          maxLength={MAX_TEXT_LENGTH}
          placeholder="Share your experience at this attraction..."
          className="focus:ring-primary-500 w-full resize-none rounded-lg border border-gray-300 px-3 py-2 focus:border-transparent focus:ring-2"
        />
        <p className="mt-1 text-right text-xs text-gray-500">
          {text.length} / {MAX_TEXT_LENGTH} characters
        </p>
      </div>

      {/* Images */}
      <div className="mb-6">
        <label className="mb-2 block text-sm font-medium text-gray-700">
          Photos (Optional)
        </label>

        {/* Image preview grid */}
        {images.length > 0 && (
          <div className="mb-3 grid grid-cols-5 gap-2">
            {images.map((image, index) => (
              <div
                key={index}
                className="group relative aspect-square overflow-hidden rounded-lg"
              >
                <img
                  src={image}
                  alt={`Preview ${index + 1}`}
                  className="h-full w-full object-cover"
                />
                <button
                  type="button"
                  className="absolute top-1 right-1 flex h-6 w-6 items-center justify-center rounded-full bg-red-500 text-white opacity-0 transition-opacity group-hover:opacity-100"
                  onClick={() => removeImage(index)}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Upload button */}
        {images.length < MAX_IMAGES && (
          <div className="relative">
            <input
              type="file"
              accept="image/*"
              className="hidden"
              id={`image-upload-${attractionId}`}
              onChange={handleImageUpload}
            />
            <label
              htmlFor={`image-upload-${attractionId}`}
              className="inline-flex cursor-pointer items-center gap-2 rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-700 transition-colors hover:bg-gray-50"
            >
              <Upload className="h-4 w-4" />
              Add Photos
            </label>
            <p className="mt-1 text-xs text-gray-500">
              {images.length} / {MAX_IMAGES} photos uploaded
            </p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <Button variant="ghost" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          variant="default"
          onClick={handleSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting
            ? "Submitting..."
            : existingReview
              ? "Update Review"
              : "Submit Review"}
        </Button>
      </div>
    </div>
  );
}
