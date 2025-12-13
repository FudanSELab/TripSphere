<script setup lang="ts">
import { Star, Upload, X } from 'lucide-vue-next'
import type { Review, CreateReviewRequest, UpdateReviewRequest } from '~/types'

interface Props {
  attractionId: string
  existingReview?: Review | null
  userId?: string // TODO: Make this required when user authentication is implemented
}

const props = withDefaults(defineProps<Props>(), {
  userId: 'user-1', // Default mock user ID - TODO: Remove when authentication is added
})

const emit = defineEmits<{
  submit: []
  cancel: []
}>()

const runtimeConfig = useRuntimeConfig()

const rating = ref(props.existingReview?.rating || 0)
const text = ref(props.existingReview?.text || '')
const images = ref<string[]>(props.existingReview?.images || [])
const isSubmitting = ref(false)
const error = ref('')

const MAX_IMAGES = 10
const MAX_TEXT_LENGTH = 2000

const setRating = (value: number) => {
  rating.value = value
}

const handleImageUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return

  const file = input.files[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    error.value = 'Please upload an image file'
    return
  }

  if (images.value.length >= MAX_IMAGES) {
    error.value = `Maximum ${MAX_IMAGES} images allowed`
    return
  }

  // In production, upload to file service and get URL
  // For now, create a local preview URL
  const reader = new FileReader()
  reader.onload = (e) => {
    if (e.target?.result) {
      images.value.push(e.target.result as string)
    }
  }
  reader.readAsDataURL(file)
  
  // Reset input
  input.value = ''
}

const removeImage = (index: number) => {
  images.value.splice(index, 1)
}

const handleSubmit = async () => {
  // Validation
  if (rating.value === 0) {
    error.value = 'Please select a rating'
    return
  }

  if (!text.value.trim()) {
    error.value = 'Please write a review'
    return
  }

  if (text.value.length > MAX_TEXT_LENGTH) {
    error.value = `Review text must be less than ${MAX_TEXT_LENGTH} characters`
    return
  }

  error.value = ''
  isSubmitting.value = true

  try {
    if (props.existingReview) {
      // Update existing review
      const updateRequest: UpdateReviewRequest = {
        id: props.existingReview.id,
        rating: rating.value,
        text: text.value,
        images: images.value,
      }
      
      // Call update API
      // await fetch(`${runtimeConfig.public.reviewServiceUrl}/reviews/${props.existingReview.id}`, {
      //   method: 'PUT',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(updateRequest),
      // })
      
      await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API call
    } else {
      // Create new review
      const createRequest: CreateReviewRequest = {
        userId: props.userId,
        targetType: 'attraction',
        targetId: props.attractionId,
        rating: rating.value,
        text: text.value,
        images: images.value,
      }
      
      // Call create API
      // await fetch(`${runtimeConfig.public.reviewServiceUrl}/reviews`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(createRequest),
      // })
      
      await new Promise(resolve => setTimeout(resolve, 500)) // Simulate API call
    }

    emit('submit')
  } catch (err) {
    error.value = 'Failed to submit review. Please try again.'
    console.error('Error submitting review:', err)
  } finally {
    isSubmitting.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
}

// Helper to check if star is filled
const isStarFilled = (index: number) => {
  return rating.value >= (index + 1)
}
</script>

<template>
  <div class="border border-gray-200 rounded-lg p-6 bg-gray-50">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">
      {{ existingReview ? 'Edit Your Review' : 'Write a Review' }}
    </h3>

    <!-- Error message -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
      {{ error }}
    </div>

    <!-- Rating -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        Rating <span class="text-red-500">*</span>
      </label>
      <div class="flex gap-1">
        <button
          v-for="i in 5"
          :key="i"
          type="button"
          :class="[
            'transition-colors',
            isStarFilled(i - 1) ? 'text-amber-400' : 'text-gray-300 hover:text-amber-300'
          ]"
          @click="setRating(i)"
        >
          <Star :class="['w-8 h-8', isStarFilled(i - 1) && 'fill-current']" />
        </button>
      </div>
      <p class="mt-1 text-xs text-gray-500">
        {{ rating === 0 ? 'Select a rating' : 
           rating <= 2 ? `${rating} star${rating > 1 ? 's' : ''} - Poor` :
           rating === 3 ? '3 stars - Average' :
           rating === 4 ? '4 stars - Good' :
           '5 stars - Excellent' }}
      </p>
    </div>

    <!-- Text content -->
    <div class="mb-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        Your Review <span class="text-red-500">*</span>
      </label>
      <textarea
        v-model="text"
        rows="6"
        :maxlength="MAX_TEXT_LENGTH"
        placeholder="Share your experience at this attraction..."
        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none"
      />
      <p class="mt-1 text-xs text-gray-500 text-right">
        {{ text.length }} / {{ MAX_TEXT_LENGTH }} characters
      </p>
    </div>

    <!-- Images -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        Photos (Optional)
      </label>
      
      <!-- Image preview grid -->
      <div v-if="images.length > 0" class="grid grid-cols-5 gap-2 mb-3">
        <div
          v-for="(image, index) in images"
          :key="index"
          class="relative aspect-square rounded-lg overflow-hidden group"
        >
          <img
            :src="image"
            :alt="`Preview ${index + 1}`"
            class="w-full h-full object-cover"
          />
          <button
            type="button"
            class="absolute top-1 right-1 w-6 h-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
            @click="removeImage(index)"
          >
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>

      <!-- Upload button -->
      <div v-if="images.length < MAX_IMAGES" class="relative">
        <input
          type="file"
          accept="image/*"
          class="hidden"
          :id="`image-upload-${attractionId}`"
          @change="handleImageUpload"
        />
        <label
          :for="`image-upload-${attractionId}`"
          class="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors cursor-pointer"
        >
          <Upload class="w-4 h-4" />
          Add Photos
        </label>
        <p class="mt-1 text-xs text-gray-500">
          {{ images.length }} / {{ MAX_IMAGES }} photos uploaded
        </p>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex gap-3 justify-end">
      <UiButton
        variant="ghost"
        @click="handleCancel"
        :disabled="isSubmitting"
      >
        Cancel
      </UiButton>
      <UiButton
        variant="primary"
        @click="handleSubmit"
        :disabled="isSubmitting"
      >
        {{ isSubmitting ? 'Submitting...' : existingReview ? 'Update Review' : 'Submit Review' }}
      </UiButton>
    </div>
  </div>
</template>
