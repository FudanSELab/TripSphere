'use client'

import { useState } from 'react'
import { Star, Upload, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { Review, CreateReviewRequest, UpdateReviewRequest } from '@/lib/types'

interface ReviewFormProps {
  attractionId: string
  existingReview?: Review | null
  userId?: string // TODO: Make this required when user authentication is implemented
  onSubmit: () => void
  onCancel: () => void
}

export function ReviewForm({
  attractionId,
  existingReview = null,
  userId = 'user-1', // Default mock user ID - TODO: Remove when authentication is added
  onSubmit,
  onCancel,
}: ReviewFormProps) {
  const [rating, setRating] = useState(existingReview?.rating || 0)
  const [text, setText] = useState(existingReview?.text || '')
  const [images, setImages] = useState<string[]>(existingReview?.images || [])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')

  const MAX_IMAGES = 10
  const MAX_TEXT_LENGTH = 2000

  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    const file = files[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file')
      return
    }

    if (images.length >= MAX_IMAGES) {
      setError(`Maximum ${MAX_IMAGES} images allowed`)
      return
    }

    // In production, upload to file service and get URL
    // For now, create a local preview URL
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        setImages([...images, e.target.result as string])
      }
    }
    reader.readAsDataURL(file)
    
    // Reset input
    event.target.value = ''
  }

  const removeImage = (index: number) => {
    setImages(images.filter((_, i) => i !== index))
  }

  const handleSubmit = async () => {
    // Validation
    if (rating === 0) {
      setError('Please select a rating')
      return
    }

    if (!text.trim()) {
      setError('Please write a review')
      return
    }

    if (text.length > MAX_TEXT_LENGTH) {
      setError(`Review text must be less than ${MAX_TEXT_LENGTH} characters`)
      return
    }

    setError('')
    setIsSubmitting(true)

    try {
      if (existingReview) {
        // Update existing review
        const updateRequest: UpdateReviewRequest = {
          id: existingReview.id,
          rating: rating,
          text: text,
          images: images,
        }
        
        // Call update API
        // await fetch(`${process.env.NEXT_PUBLIC_REVIEW_SERVICE_URL}/reviews/${existingReview.id}`, {
        //   method: 'PUT',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(updateRequest),
        // })
        
        await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API call
      } else {
        // Create new review
        const createRequest: CreateReviewRequest = {
          userId: userId,
          targetType: 'attraction',
          targetId: attractionId,
          rating: rating,
          text: text,
          images: images,
        }
        
        // Call create API
        // await fetch(`${process.env.NEXT_PUBLIC_REVIEW_SERVICE_URL}/reviews`, {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify(createRequest),
        // })
        
        await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API call
      }

      onSubmit()
    } catch (err) {
      setError('Failed to submit review. Please try again.')
      console.error('Error submitting review:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  // Helper to check if star is filled
  const isStarFilled = (index: number) => {
    return rating >= (index + 1)
  }

  return (
    <div className="border border-gray-200 rounded-lg p-6 bg-gray-50">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        {existingReview ? 'Edit Your Review' : 'Write a Review'}
      </h3>

      {/* Error message */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      {/* Rating */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Rating <span className="text-red-500">*</span>
        </label>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((i) => (
            <button
              key={i}
              type="button"
              className={`transition-colors ${
                isStarFilled(i - 1) ? 'text-amber-400' : 'text-gray-300 hover:text-amber-300'
              }`}
              onClick={() => setRating(i)}
            >
              <Star className={`w-8 h-8 ${isStarFilled(i - 1) ? 'fill-current' : ''}`} />
            </button>
          ))}
        </div>
        <p className="mt-1 text-xs text-gray-500">
          {rating === 0 ? 'Select a rating' : 
           rating <= 2 ? `${rating} star${rating > 1 ? 's' : ''} - Poor` :
           rating === 3 ? '3 stars - Average' :
           rating === 4 ? '4 stars - Good' :
           '5 stars - Excellent'}
        </p>
      </div>

      {/* Text content */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Your Review <span className="text-red-500">*</span>
        </label>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={6}
          maxLength={MAX_TEXT_LENGTH}
          placeholder="Share your experience at this attraction..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
        />
        <p className="mt-1 text-xs text-gray-500 text-right">
          {text.length} / {MAX_TEXT_LENGTH} characters
        </p>
      </div>

      {/* Images */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Photos (Optional)
        </label>
        
        {/* Image preview grid */}
        {images.length > 0 && (
          <div className="grid grid-cols-5 gap-2 mb-3">
            {images.map((image, index) => (
              <div
                key={index}
                className="relative aspect-square rounded-lg overflow-hidden group"
              >
                <img
                  src={image}
                  alt={`Preview ${index + 1}`}
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  className="absolute top-1 right-1 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={() => removeImage(index)}
                >
                  <X className="w-4 h-4" />
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
              className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <Upload className="w-4 h-4" />
              Add Photos
            </label>
            <p className="mt-1 text-xs text-gray-500">
              {images.length} / {MAX_IMAGES} photos uploaded
            </p>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3 justify-end">
        <Button
          variant="ghost"
          onClick={onCancel}
          disabled={isSubmitting}
        >
          Cancel
        </Button>
        <Button
          variant="default"
          onClick={handleSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : existingReview ? 'Update Review' : 'Submit Review'}
        </Button>
      </div>
    </div>
  )
}
