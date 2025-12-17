<script setup lang="ts">
import { MapPin, Star, Clock, Ticket, ChevronLeft, Share2, Heart, MessageCircle, Cloud } from 'lucide-vue-next'
import ReviewForm from '~/components/reviews/ReviewForm.vue'
import ChatSidebar from '~/components/chat/ChatSidebar.vue'
import type { Attraction, Review, ChatContext } from '~/types'

definePageMeta({
  layout: 'default',
})

const route = useRoute()
const attractionId = route.params.id as string
// TODO: Replace with real authentication when user service is integrated
const currentUser = ref({ id: 'user-1', username: 'Demo User' })

// Chat sidebar state
const isChatSidebarOpen = ref(false)
const chatContext = ref<ChatContext | null>(null)
const chatTitle = ref('AI Assistant')

// Mock attraction data (in production, this would be fetched from the API)
const attraction = ref<Attraction>({
  id: attractionId,
  name: 'The Bund',
  description: 'The Bund is a waterfront area in central Shanghai, featuring a mix of historical colonial-era buildings and modern skyscrapers. It offers stunning views of the Huangpu River and the futuristic Pudong skyline across the water. A must-visit destination for any traveler to Shanghai, the Bund combines history, architecture, and vibrant city life.',
  address: { 
    country: 'China', 
    province: 'Shanghai', 
    city: 'Shanghai', 
    county: 'Huangpu', 
    district: '', 
    street: 'Zhongshan East 1st Road' 
  },
  location: { lng: 121.4883, lat: 31.2319 },
  category: 'Landmark',
  rating: 4.8,
  openingHours: '24 hours',
  ticketPrice: 'Free',
  images: [
    'https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=1200&h=800&fit=crop',
    'https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=1200&h=800&fit=crop',
    'https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=1200&h=800&fit=crop',
  ],
  tags: ['Historic', 'Scenic', 'Night View', 'Photography'],
})

const selectedImageIndex = ref(0)
const showReviewForm = ref(false)
const reviews = ref<Review[]>([])
const reviewsLoading = ref(false)
const userReview = ref<Review | null>(null)

// Fetch reviews
const fetchReviews = async () => {
  reviewsLoading.value = true
  try {
    // This would call the actual API
    // const response = await fetch(`${runtimeConfig.public.reviewServiceUrl}/reviews?targetType=attraction&targetId=${attractionId}`)
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
    
    reviews.value = mockReviews
    
    // Check if current user has reviewed
    userReview.value = mockReviews.find(r => r.userId === currentUser.value.id) || null
  } finally {
    reviewsLoading.value = false
  }
}

const handleReviewSubmit = () => {
  showReviewForm.value = false
  fetchReviews()
}

const handleReviewEdit = () => {
  showReviewForm.value = true
}

const openReviewForm = () => {
  showReviewForm.value = true
}

const closeReviewForm = () => {
  showReviewForm.value = false
}

const handleReviewDelete = async () => {
  if (confirm('Are you sure you want to delete your review?')) {
    // Call delete API
    userReview.value = null
    fetchReviews()
  }
}

const handleAskAboutReviews = () => {
  // Open chat sidebar with review context
  chatContext.value = {
    type: 'review-summary',
    targetType: 'attraction',
    targetId: attractionId,
    attractionName: attraction.value.name,
  }
  chatTitle.value = `Reviews for ${attraction.value.name}`
  isChatSidebarOpen.value = true
}

// Weather & Tips - Auto-send query with journey_assistant agent
const handleWeatherAndTips = () => {
  // Prepare the query template with attraction info
  const query = `请帮我查询${attraction.value.name}（位于${attraction.value.address.city}，${attraction.value.address.country}）的天气情况和旅行建议。`
  
  // Set chat context with auto-send configuration
  chatContext.value = {
    type: 'attraction',
    targetType: 'attraction',
    targetId: attractionId,
    attractionName: attraction.value.name,
    agent: 'journey_assistant', // Route to journey_assistant agent
    autoSendQuery: query,
    autoSendMetadata: {
      agent: 'journey_assistant', // This will route to journey_assistant in facade.py
    },
  }
  chatTitle.value = `Weather & Tips: ${attraction.value.name}`
  isChatSidebarOpen.value = true
}

const closeChatSidebar = () => {
  isChatSidebarOpen.value = false
  // Reset chat context to allow creating a new conversation next time
  chatContext.value = null
}

onMounted(() => {
  fetchReviews()
})

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
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Back button -->
    <div class="bg-white border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <NuxtLink 
          to="/attractions" 
          class="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ChevronLeft class="w-5 h-5" />
          Back to Attractions
        </NuxtLink>
      </div>
    </div>

    <!-- Main content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid lg:grid-cols-3 gap-8">
        <!-- Left column - Main content -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Image gallery -->
          <div class="bg-white rounded-xl shadow-sm overflow-hidden">
            <div class="aspect-[16/9] relative">
              <img
                :src="attraction.images?.[selectedImageIndex]"
                :alt="attraction.name"
                class="w-full h-full object-cover"
              />
            </div>
            <div v-if="attraction.images && attraction.images.length > 1" class="p-4">
              <div class="flex gap-2 overflow-x-auto">
                <button
                  v-for="(image, index) in attraction.images"
                  :key="index"
                  :class="[
                    'flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 transition-all',
                    selectedImageIndex === index
                      ? 'border-primary-600 ring-2 ring-primary-600/20'
                      : 'border-gray-200 hover:border-gray-300'
                  ]"
                  @click="selectedImageIndex = index"
                >
                  <img
                    :src="image"
                    :alt="`${attraction.name} - Image ${index + 1}`"
                    class="w-full h-full object-cover"
                  />
                </button>
              </div>
            </div>
          </div>

          <!-- Basic info -->
          <div class="bg-white rounded-xl shadow-sm p-6">
            <div class="flex items-start justify-between mb-4">
              <div>
                <div class="flex items-center gap-2 mb-2">
                  <UiBadge variant="default" size="md">
                    {{ attraction.category }}
                  </UiBadge>
                  <div v-if="attraction.tags" class="flex gap-2">
                    <UiBadge
                      v-for="tag in attraction.tags.slice(0, 3)"
                      :key="tag"
                      variant="secondary"
                      size="sm"
                    >
                      {{ tag }}
                    </UiBadge>
                  </div>
                </div>
                <div class="flex items-center gap-3 mb-2">
                  <h1 class="text-3xl font-bold text-gray-900">
                    {{ attraction.name }}
                  </h1>
                  <UiButton
                    variant="outline"
                    size="sm"
                    @click="handleWeatherAndTips"
                    class="flex items-center gap-2"
                  >
                    <Cloud class="w-4 h-4" />
                    Weather & Tips
                  </UiButton>
                </div>
                <div class="flex items-center gap-4 text-sm text-gray-600">
                  <div class="flex items-center gap-1">
                    <MapPin class="w-4 h-4" />
                    {{ attraction.address.city }}, {{ attraction.address.country }}
                  </div>
                  <div v-if="attraction.rating" class="flex items-center gap-1 text-amber-500">
                    <Star class="w-4 h-4 fill-current" />
                    <span class="font-medium text-gray-900">{{ attraction.rating }}</span>
                  </div>
                </div>
              </div>
              <div class="flex gap-2">
                <button
                  class="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-gray-600 transition-colors"
                  title="Share"
                >
                  <Share2 class="w-5 h-5" />
                </button>
                <button
                  class="w-10 h-10 rounded-full bg-gray-100 hover:bg-red-50 flex items-center justify-center text-gray-600 hover:text-red-500 transition-colors"
                  title="Add to favorites"
                >
                  <Heart class="w-5 h-5" />
                </button>
              </div>
            </div>

            <div class="border-t border-gray-100 pt-4">
              <h2 class="text-lg font-semibold text-gray-900 mb-3">About</h2>
              <p class="text-gray-600 leading-relaxed">
                {{ attraction.description }}
              </p>
            </div>

            <div class="border-t border-gray-100 mt-6 pt-6">
              <h2 class="text-lg font-semibold text-gray-900 mb-4">Address</h2>
              <p class="text-gray-600">
                {{ attraction.address.street }}<br>
                {{ attraction.address.county }}, {{ attraction.address.city }}<br>
                {{ attraction.address.province }}, {{ attraction.address.country }}
              </p>
            </div>
          </div>

          <!-- Reviews Section -->
          <div id="reviews" class="bg-white rounded-xl shadow-sm p-6">
            <div class="flex items-center justify-between mb-6">
              <h2 class="text-2xl font-bold text-gray-900">Reviews</h2>
              <div class="flex gap-3">
                <UiButton
                  variant="outline"
                  size="sm"
                  @click="handleAskAboutReviews"
                >
                  <MessageCircle class="w-4 h-4 mr-2" />
                  Ask About Reviews
                </UiButton>
                <UiButton
                  v-if="!userReview"
                  variant="primary"
                  size="sm"
                  @click="openReviewForm"
                >
                  Write a Review
                </UiButton>
              </div>
            </div>

            <!-- Review Form -->
            <div v-if="showReviewForm" class="mb-6">
              <ReviewForm
                :attraction-id="attractionId"
                :user-id="currentUser.id"
                :existing-review="userReview"
                @submit="handleReviewSubmit"
                @cancel="closeReviewForm"
              />
            </div>

            <!-- User's own review (shown at top) -->
            <div v-if="userReview && !showReviewForm" class="mb-6">
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-start justify-between mb-3">
                  <div>
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-semibold text-gray-900">Your Review</span>
                      <div class="flex gap-0.5">
                        <Star
                          v-for="(filled, index) in getRatingStars(userReview.rating)"
                          :key="index"
                          :class="['w-4 h-4', filled ? 'text-amber-400 fill-current' : 'text-gray-300']"
                        />
                      </div>
                    </div>
                    <p class="text-sm text-gray-500">{{ formatDate(userReview.createdAt) }}</p>
                  </div>
                  <div class="flex gap-2">
                    <UiButton variant="ghost" size="sm" @click="handleReviewEdit">
                      Edit
                    </UiButton>
                    <UiButton variant="ghost" size="sm" @click="handleReviewDelete">
                      Delete
                    </UiButton>
                  </div>
                </div>
                <p class="text-gray-700 mb-3">{{ userReview.text }}</p>
                <div v-if="userReview.images.length > 0" class="flex gap-2 flex-wrap">
                  <img
                    v-for="(image, index) in userReview.images"
                    :key="index"
                    :src="image"
                    :alt="`Review image ${index + 1}`"
                    class="w-24 h-24 object-cover rounded-lg"
                  />
                </div>
              </div>
            </div>

            <!-- Other reviews -->
            <div v-if="reviewsLoading" class="text-center py-8">
              <p class="text-gray-500">Loading reviews...</p>
            </div>
            <div v-else-if="reviews.length === 0" class="text-center py-8">
              <p class="text-gray-500">No reviews yet. Be the first to review!</p>
            </div>
            <div v-else class="space-y-6">
              <div
                v-for="review in reviews.filter(r => r.userId !== currentUser.id)"
                :key="review.id"
                class="border-b border-gray-100 pb-6 last:border-0"
              >
                <div class="flex items-start gap-4">
                  <div class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center">
                    <span class="text-sm font-medium text-gray-600">U</span>
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-semibold text-gray-900">User {{ review.userId.slice(-1) }}</span>
                      <div class="flex gap-0.5">
                        <Star
                          v-for="(filled, index) in getRatingStars(review.rating)"
                          :key="index"
                          :class="['w-4 h-4', filled ? 'text-amber-400 fill-current' : 'text-gray-300']"
                        />
                      </div>
                    </div>
                    <p class="text-sm text-gray-500 mb-3">{{ formatDate(review.createdAt) }}</p>
                    <p class="text-gray-700 mb-3">{{ review.text }}</p>
                    <div v-if="review.images.length > 0" class="flex gap-2 flex-wrap">
                      <img
                        v-for="(image, index) in review.images"
                        :key="index"
                        :src="image"
                        :alt="`Review image ${index + 1}`"
                        class="w-24 h-24 object-cover rounded-lg"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right column - Sidebar info -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-xl shadow-sm p-6 sticky top-8">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Visit Information</h3>
            
            <div class="space-y-4">
              <div class="flex items-start gap-3">
                <Clock class="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <p class="font-medium text-gray-900">Opening Hours</p>
                  <p class="text-sm text-gray-600">{{ attraction.openingHours }}</p>
                </div>
              </div>

              <div class="flex items-start gap-3">
                <Ticket class="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <p class="font-medium text-gray-900">Ticket Price</p>
                  <p class="text-sm text-gray-600">{{ attraction.ticketPrice }}</p>
                </div>
              </div>

              <div class="flex items-start gap-3">
                <MapPin class="w-5 h-5 text-gray-400 mt-0.5" />
                <div>
                  <p class="font-medium text-gray-900">Location</p>
                  <p class="text-sm text-gray-600">
                    {{ attraction.location.lat.toFixed(4) }}, {{ attraction.location.lng.toFixed(4) }}
                  </p>
                </div>
              </div>
            </div>

            <div class="mt-6 pt-6 border-t border-gray-100">
              <UiButton variant="primary" class="w-full">
                Get Directions
              </UiButton>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chat Sidebar -->
    <ChatSidebar
      :is-open="isChatSidebarOpen"
      :initial-context="chatContext"
      :title="chatTitle"
      @close="closeChatSidebar"
    />
  </div>
</template>
