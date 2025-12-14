'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { MapPin, Star, Clock, Ticket, ChevronLeft, Share2, Heart, MessageCircle } from 'lucide-react'
import { useParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ReviewForm } from '@/components/reviews/review-form'
import { useAttractions } from '@/lib/hooks/use-attractions'
import type { Attraction, Review, ChatContext } from '@/lib/types'

export default function AttractionDetailPage() {
  const params = useParams()
  const attractionId = params.id as string
  const { fetchAttraction } = useAttractions()
  
  // TODO: Replace with real authentication when user service is integrated
  const currentUser = { id: 'user-1', username: 'Demo User' }

  // State
  const [attraction, setAttraction] = useState<Attraction | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedImageIndex, setSelectedImageIndex] = useState(0)
  const [showReviewForm, setShowReviewForm] = useState(false)
  const [reviews, setReviews] = useState<Review[]>([])
  const [reviewsLoading, setReviewsLoading] = useState(false)
  const [userReview, setUserReview] = useState<Review | null>(null)

  // Chat sidebar state (TODO: implement when chat component is ready)
  const [isChatSidebarOpen, setIsChatSidebarOpen] = useState(false)
  const [chatContext, setChatContext] = useState<ChatContext | null>(null)
  const [chatTitle, setChatTitle] = useState('AI Assistant')

  // Fetch attraction data
  useEffect(() => {
    const loadAttraction = async () => {
      try {
        const data = await fetchAttraction(attractionId)
        setAttraction(data)
      } catch (error) {
        console.error('Error loading attraction:', error)
      } finally {
        setLoading(false)
      }
    }

    loadAttraction()
  }, [attractionId])

  // Fetch reviews
  const fetchReviews = async () => {
    setReviewsLoading(true)
    try {
      // This would call the actual API
      // const response = await fetch(`${process.env.NEXT_PUBLIC_REVIEW_SERVICE_URL}/reviews?targetType=attraction&targetId=${attractionId}`)
      // For now, using mock data
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Mock reviews data
      const mockReviews: Review[] = [
        {
          id: 'review-1',
          userId: 'user-2',
          targetType: 'attraction',
          targetId: attractionId,
          rating: 5,
          text: 'Absolutely stunning views, especially at night! The historic buildings are beautifully preserved and the modern skyline across the river is breathtaking.',
          images: ['https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=400&h=300&fit=crop'],
          createdAt: Date.now() - 86400000 * 2,
          updatedAt: Date.now() - 86400000 * 2,
        },
        {
          id: 'review-2',
          userId: 'user-3',
          targetType: 'attraction',
          targetId: attractionId,
          rating: 4,
          text: 'Great place for a walk along the waterfront. Very crowded during weekends and holidays though.',
          images: [],
          createdAt: Date.now() - 86400000 * 5,
          updatedAt: Date.now() - 86400000 * 5,
        },
        {
          id: 'review-3',
          userId: 'user-4',
          targetType: 'attraction',
          targetId: attractionId,
          rating: 5,
          text: 'Perfect spot for photography! Visited during sunset and the golden hour lighting was amazing.',
          images: [
            'https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=400&h=300&fit=crop',
            'https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=400&h=300&fit=crop'
          ],
          createdAt: Date.now() - 86400000 * 7,
          updatedAt: Date.now() - 86400000 * 7,
        },
      ]
      
      setReviews(mockReviews)
      
      // Check if current user has reviewed
      setUserReview(mockReviews.find(r => r.userId === currentUser.id) || null)
    } finally {
      setReviewsLoading(false)
    }
  }

  useEffect(() => {
    fetchReviews()
  }, [attractionId])

  const handleReviewSubmit = () => {
    setShowReviewForm(false)
    fetchReviews()
  }

  const handleReviewEdit = () => {
    setShowReviewForm(true)
  }

  const openReviewForm = () => {
    setShowReviewForm(true)
  }

  const closeReviewForm = () => {
    setShowReviewForm(false)
  }

  const handleReviewDelete = async () => {
    if (confirm('Are you sure you want to delete your review?')) {
      // Call delete API
      setUserReview(null)
      fetchReviews()
    }
  }

  const handleAskAboutReviews = () => {
    // Open chat sidebar with review context
    if (attraction) {
      setChatContext({
        type: 'review-summary',
        targetType: 'attraction',
        targetId: attractionId,
        attractionName: attraction.name,
      })
      setChatTitle(`Reviews for ${attraction.name}`)
      setIsChatSidebarOpen(true)
    }
  }

  const closeChatSidebar = () => {
    setIsChatSidebarOpen(false)
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    })
  }

  const getRatingStars = (rating: number) => {
    return Array(5).fill(0).map((_, i) => i < rating)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-20 h-20 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-6 animate-pulse">
            <div className="w-10 h-10 border-4 border-primary-600 border-t-transparent rounded-full animate-spin" />
          </div>
          <p className="text-gray-600 font-medium">Loading attraction details...</p>
          <p className="text-gray-400 text-sm mt-2">Please wait a moment</p>
        </div>
      </div>
    )
  }

  if (!attraction) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500 mb-4">Attraction not found</p>
          <Link href="/attractions">
            <Button variant="default">Back to Attractions</Button>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Back button */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <Link 
            href="/attractions" 
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
            Back to Attractions
          </Link>
        </div>
      </div>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Left column - Main content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Image gallery */}
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="aspect-[16/9] relative">
                <img
                  src={attraction.images?.[selectedImageIndex]}
                  alt={attraction.name}
                  className="w-full h-full object-cover"
                />
              </div>
              {attraction.images && attraction.images.length > 1 && (
                <div className="p-4">
                  <div className="flex gap-2 overflow-x-auto">
                    {attraction.images.map((image, index) => (
                      <button
                        key={index}
                        className={`flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all ${
                          selectedImageIndex === index
                            ? 'border-primary-600 ring-2 ring-primary-600/20'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setSelectedImageIndex(index)}
                      >
                        <img
                          src={image}
                          alt={`${attraction.name} - Image ${index + 1}`}
                          className="w-full h-full object-cover"
                        />
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Basic info */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="default">
                      {attraction.category}
                    </Badge>
                    {attraction.tags && (
                      <div className="flex gap-2">
                        {attraction.tags.slice(0, 3).map((tag) => (
                          <Badge key={tag} variant="secondary">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <h1 className="text-3xl font-bold text-gray-900 mb-2">
                    {attraction.name}
                  </h1>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <MapPin className="w-4 h-4" />
                      {attraction.address.city}, {attraction.address.country}
                    </div>
                    {attraction.rating && (
                      <div className="flex items-center gap-1 text-amber-500">
                        <Star className="w-4 h-4 fill-current" />
                        <span className="font-medium text-gray-900">{attraction.rating}</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    className="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 transition-colors"
                    title="Share"
                  >
                    <Share2 className="w-5 h-5" />
                  </button>
                  <button
                    className="w-10 h-10 rounded-full bg-gray-100 hover:bg-red-50 flex items-center justify-center text-gray-600 hover:text-red-500 transition-colors"
                    title="Add to favorites"
                  >
                    <Heart className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="border-t border-gray-100 pt-4">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">About</h2>
                <p className="text-gray-600 leading-relaxed">
                  {attraction.description}
                </p>
              </div>

              <div className="border-t border-gray-100 mt-6 pt-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Address</h2>
                <p className="text-gray-600">
                  {attraction.address.street}<br />
                  {attraction.address.county}, {attraction.address.city}<br />
                  {attraction.address.province}, {attraction.address.country}
                </p>
              </div>
            </div>

            {/* Reviews Section */}
            <div id="reviews" className="bg-white rounded-xl shadow-sm p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">Reviews</h2>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={handleAskAboutReviews}
                  >
                    <MessageCircle className="w-4 h-4 mr-2" />
                    Ask About Reviews
                  </Button>
                  {!userReview && (
                    <Button
                      variant="default"
                      onClick={openReviewForm}
                    >
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
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-gray-900">Your Review</span>
                          <div className="flex gap-0.5">
                            {getRatingStars(userReview.rating).map((filled, index) => (
                              <Star
                                key={index}
                                className={`w-4 h-4 ${filled ? 'text-amber-400 fill-current' : 'text-gray-300'}`}
                              />
                            ))}
                          </div>
                        </div>
                        <p className="text-sm text-gray-500">{formatDate(userReview.createdAt)}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="ghost" size="sm" onClick={handleReviewEdit}>
                          Edit
                        </Button>
                        <Button variant="ghost" size="sm" onClick={handleReviewDelete}>
                          Delete
                        </Button>
                      </div>
                    </div>
                    <p className="text-gray-700 mb-3">{userReview.text}</p>
                    {userReview.images.length > 0 && (
                      <div className="flex gap-2 flex-wrap">
                        {userReview.images.map((image, index) => (
                          <img
                            key={index}
                            src={image}
                            alt={`Review image ${index + 1}`}
                            className="w-24 h-24 object-cover rounded-lg"
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Other reviews */}
              {reviewsLoading ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">Loading reviews...</p>
                </div>
              ) : reviews.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500">No reviews yet. Be the first to review!</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {reviews
                    .filter(r => r.userId !== currentUser.id)
                    .map((review) => (
                      <div
                        key={review.id}
                        className="border-b border-gray-100 pb-6 last:border-0"
                      >
                        <div className="flex items-start gap-4">
                          <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                            <span className="text-sm font-medium text-gray-600">U</span>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-semibold text-gray-900">
                                User {review.userId.slice(-1)}
                              </span>
                              <div className="flex gap-0.5">
                                {getRatingStars(review.rating).map((filled, index) => (
                                  <Star
                                    key={index}
                                    className={`w-4 h-4 ${filled ? 'text-amber-400 fill-current' : 'text-gray-300'}`}
                                  />
                                ))}
                              </div>
                            </div>
                            <p className="text-sm text-gray-500 mb-3">{formatDate(review.createdAt)}</p>
                            <p className="text-gray-700 mb-3">{review.text}</p>
                            {review.images.length > 0 && (
                              <div className="flex gap-2 flex-wrap">
                                {review.images.map((image, index) => (
                                  <img
                                    key={index}
                                    src={image}
                                    alt={`Review image ${index + 1}`}
                                    className="w-24 h-24 object-cover rounded-lg"
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
            <div className="bg-white rounded-xl shadow-sm p-6 sticky top-22">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Visit Information</h3>
              
              <div className="space-y-4">
                <div className="flex items-start gap-3">
                  <Clock className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Opening Hours</p>
                    <p className="text-sm text-gray-600">{attraction.openingHours}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Ticket className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Ticket Price</p>
                    <p className="text-sm text-gray-600">{attraction.ticketPrice}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-gray-400 mt-0.5" />
                  <div>
                    <p className="font-medium text-gray-900">Location</p>
                    <p className="text-sm text-gray-600">
                      {attraction.location.lat.toFixed(4)}, {attraction.location.lng.toFixed(4)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-6 border-t border-gray-100">
                <Button variant="default" className="w-full">
                  Get Directions
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Sidebar - TODO: Implement when chat component is ready */}
      {/* <ChatSidebar
        isOpen={isChatSidebarOpen}
        initialContext={chatContext}
        title={chatTitle}
        onClose={closeChatSidebar}
      /> */}
    </div>
  )
}
