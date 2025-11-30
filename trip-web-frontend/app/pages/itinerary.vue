<script setup lang="ts">
import { 
  Calendar,
  MapPin,
  Clock,
  Plus,
  ChevronRight,
  ChevronDown,
  Sparkles,
  Loader2,
  GripVertical,
  Trash2,
  Edit3,
  Save
} from 'lucide-vue-next'
import type { Itinerary, DayPlan, Activity } from '~/types'

definePageMeta({
  layout: 'default',
})

// Form state
const form = reactive({
  destination: '',
  startDate: '',
  endDate: '',
  interests: [] as string[],
  budgetLevel: 'moderate' as 'budget' | 'moderate' | 'luxury',
  numTravelers: 2,
})

const availableInterests = [
  'Culture', 'Food', 'Nature', 'Adventure', 'Shopping', 
  'History', 'Art', 'Nightlife', 'Family', 'Photography'
]

const budgetOptions = [
  { value: 'budget', label: 'Budget', description: 'Economical options' },
  { value: 'moderate', label: 'Moderate', description: 'Balanced comfort' },
  { value: 'luxury', label: 'Luxury', description: 'Premium experience' },
]

// Generated itinerary state
const itinerary = ref<Itinerary | null>(null)
const isGenerating = ref(false)
const generationProgress = ref(0)
const generationStatus = ref('')
const expandedDays = ref<number[]>([1])

// Toggle interest selection
const toggleInterest = (interest: string) => {
  const index = form.interests.indexOf(interest)
  if (index > -1) {
    form.interests.splice(index, 1)
  } else {
    form.interests.push(interest)
  }
}

// Generate itinerary
const generateItinerary = async () => {
  if (!form.destination || !form.startDate || !form.endDate) {
    return
  }

  isGenerating.value = true
  generationProgress.value = 0
  generationStatus.value = 'Analyzing your preferences...'

  // Simulate AI generation with progress
  const steps = [
    { progress: 20, status: 'Researching destination...' },
    { progress: 40, status: 'Finding best attractions...' },
    { progress: 60, status: 'Optimizing route...' },
    { progress: 80, status: 'Adding recommendations...' },
    { progress: 100, status: 'Finalizing itinerary...' },
  ]

  for (const step of steps) {
    await new Promise(resolve => setTimeout(resolve, 800))
    generationProgress.value = step.progress
    generationStatus.value = step.status
  }

  // Mock generated itinerary
  const startDate = new Date(form.startDate)
  const endDate = new Date(form.endDate)
  const numDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24)) + 1

  const mockDayPlans: DayPlan[] = Array.from({ length: numDays }, (_, i) => {
    const date = new Date(startDate)
    date.setDate(date.getDate() + i)
    
    return {
      dayNumber: i + 1,
      date: date.toISOString().split('T')[0],
      activities: [
        {
          id: `${i}-1`,
          name: i === 0 ? 'Arrival & Check-in' : `Morning at ${['West Lake', 'The Bund', 'Yu Garden', 'Temple'][i % 4]}`,
          description: 'Start your day with a visit to this iconic location.',
          startTime: '09:00',
          endTime: '12:00',
          location: { name: form.destination, latitude: 31.23, longitude: 121.47, address: form.destination },
          category: 'sightseeing',
          cost: { amount: 0, currency: 'CNY' },
        },
        {
          id: `${i}-2`,
          name: `Lunch at Local Restaurant`,
          description: 'Enjoy authentic local cuisine at a recommended restaurant.',
          startTime: '12:30',
          endTime: '14:00',
          location: { name: 'Local Restaurant', latitude: 31.23, longitude: 121.47, address: form.destination },
          category: 'dining',
          cost: { amount: 150, currency: 'CNY' },
        },
        {
          id: `${i}-3`,
          name: i === numDays - 1 ? 'Departure' : `Afternoon at ${['Shopping District', 'Museum', 'Park', 'Landmark'][i % 4]}`,
          description: 'Continue exploring the city and its attractions.',
          startTime: '15:00',
          endTime: '18:00',
          location: { name: form.destination, latitude: 31.23, longitude: 121.47, address: form.destination },
          category: i === numDays - 1 ? 'transportation' : 'sightseeing',
          cost: { amount: 80, currency: 'CNY' },
        },
      ],
      notes: i === 0 ? 'Remember to exchange currency and get a local SIM card.' : '',
    }
  })

  itinerary.value = {
    id: 'itinerary-' + Date.now(),
    destination: form.destination,
    startDate: form.startDate,
    endDate: form.endDate,
    dayPlans: mockDayPlans,
    summary: {
      totalEstimatedCost: numDays * 230,
      currency: 'CNY',
      totalActivities: numDays * 3,
      highlights: ['Local cuisine experience', 'Cultural immersion', 'Scenic landmarks'],
    },
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }

  expandedDays.value = [1]
  isGenerating.value = false
}

// Toggle day expansion
const toggleDay = (dayNumber: number) => {
  const index = expandedDays.value.indexOf(dayNumber)
  if (index > -1) {
    expandedDays.value.splice(index, 1)
  } else {
    expandedDays.value.push(dayNumber)
  }
}

// Format date for display
const formatDayDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

// Get activity category color
const getCategoryColor = (category: string) => {
  const colors: Record<string, string> = {
    sightseeing: 'bg-blue-100 text-blue-700',
    dining: 'bg-orange-100 text-orange-700',
    transportation: 'bg-gray-100 text-gray-700',
    shopping: 'bg-pink-100 text-pink-700',
    entertainment: 'bg-purple-100 text-purple-700',
  }
  return colors[category] || 'bg-gray-100 text-gray-700'
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Hero section -->
    <div class="bg-gradient-to-br from-green-600 to-emerald-600 text-white py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center animate-fade-in-up">
          <span class="inline-flex items-center gap-2 px-4 py-2 bg-white/20 rounded-full text-sm font-medium mb-4">
            <Sparkles class="w-4 h-4" />
            AI-Powered Planning
          </span>
          <h1 class="text-4xl sm:text-5xl font-bold mb-4">Plan Your Perfect Trip</h1>
          <p class="text-xl text-white/80 max-w-2xl mx-auto">
            Let our AI create a personalized itinerary based on your preferences, interests, and travel style.
          </p>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="grid lg:grid-cols-3 gap-8">
        <!-- Planning form -->
        <div class="lg:col-span-1">
          <UiCard class="sticky top-24">
            <h2 class="text-xl font-semibold text-gray-900 mb-6">Trip Details</h2>
            
            <form class="space-y-5" @submit.prevent="generateItinerary">
              <!-- Destination -->
              <UiInput
                v-model="form.destination"
                label="Destination"
                placeholder="e.g., Shanghai, China"
              >
                <template #prepend>
                  <MapPin class="w-5 h-5" />
                </template>
              </UiInput>

              <!-- Dates -->
              <div class="grid grid-cols-2 gap-3">
                <UiInput
                  v-model="form.startDate"
                  type="date"
                  label="Start Date"
                />
                <UiInput
                  v-model="form.endDate"
                  type="date"
                  label="End Date"
                />
              </div>

              <!-- Travelers -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Number of Travelers
                </label>
                <div class="flex items-center gap-3">
                  <button
                    type="button"
                    class="w-10 h-10 rounded-lg border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-50"
                    :disabled="form.numTravelers <= 1"
                    @click="form.numTravelers = Math.max(1, form.numTravelers - 1)"
                  >
                    -
                  </button>
                  <span class="text-lg font-medium text-gray-900 w-8 text-center">
                    {{ form.numTravelers }}
                  </span>
                  <button
                    type="button"
                    class="w-10 h-10 rounded-lg border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-50"
                    @click="form.numTravelers++"
                  >
                    +
                  </button>
                </div>
              </div>

              <!-- Budget level -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Budget Level
                </label>
                <div class="grid grid-cols-3 gap-2">
                  <button
                    v-for="option in budgetOptions"
                    :key="option.value"
                    type="button"
                    :class="[
                      'p-3 rounded-lg border text-center transition-all',
                      form.budgetLevel === option.value
                        ? 'border-green-500 bg-green-50 text-green-700'
                        : 'border-gray-200 hover:border-gray-300'
                    ]"
                    @click="form.budgetLevel = option.value as any"
                  >
                    <div class="text-sm font-medium">{{ option.label }}</div>
                  </button>
                </div>
              </div>

              <!-- Interests -->
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                  Interests
                </label>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="interest in availableInterests"
                    :key="interest"
                    type="button"
                    :class="[
                      'px-3 py-1.5 rounded-full text-sm font-medium transition-all',
                      form.interests.includes(interest)
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    ]"
                    @click="toggleInterest(interest)"
                  >
                    {{ interest }}
                  </button>
                </div>
              </div>

              <!-- Generate button -->
              <UiButton
                type="submit"
                class="w-full"
                size="lg"
                :loading="isGenerating"
                :disabled="!form.destination || !form.startDate || !form.endDate"
              >
                <Sparkles class="w-5 h-5" />
                Generate Itinerary
              </UiButton>
            </form>
          </UiCard>
        </div>

        <!-- Itinerary display -->
        <div class="lg:col-span-2">
          <!-- Loading state -->
          <div
            v-if="isGenerating"
            class="text-center py-16"
          >
            <div class="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
              <Loader2 class="w-10 h-10 text-green-600 animate-spin" />
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-2">
              {{ generationStatus }}
            </h3>
            <div class="w-64 h-2 bg-gray-200 rounded-full mx-auto overflow-hidden">
              <div
                class="h-full bg-green-600 rounded-full transition-all duration-500"
                :style="{ width: `${generationProgress}%` }"
              />
            </div>
            <p class="text-gray-500 mt-4">
              This may take a moment...
            </p>
          </div>

          <!-- Empty state -->
          <div
            v-else-if="!itinerary"
            class="text-center py-16"
          >
            <div class="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6 animate-float">
              <Calendar class="w-10 h-10 text-green-600" />
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-2">
              Ready to plan your trip?
            </h3>
            <p class="text-gray-500 max-w-md mx-auto">
              Fill in your trip details on the left and let our AI create a personalized itinerary just for you.
            </p>
          </div>

          <!-- Generated itinerary -->
          <div v-else class="space-y-6 animate-fade-in-up">
            <!-- Summary card -->
            <UiCard>
              <div class="flex items-start justify-between">
                <div>
                  <h2 class="text-2xl font-bold text-gray-900">
                    {{ itinerary.destination }}
                  </h2>
                  <p class="text-gray-500 mt-1">
                    {{ formatDayDate(itinerary.startDate) }} - {{ formatDayDate(itinerary.endDate) }}
                  </p>
                </div>
                <div class="flex gap-2">
                  <UiButton variant="outline" size="sm">
                    <Edit3 class="w-4 h-4" />
                    Edit
                  </UiButton>
                  <UiButton variant="default" size="sm">
                    <Save class="w-4 h-4" />
                    Save
                  </UiButton>
                </div>
              </div>

              <!-- Summary stats -->
              <div class="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100">
                <div class="text-center">
                  <div class="text-2xl font-bold text-gray-900">
                    {{ itinerary.dayPlans.length }}
                  </div>
                  <div class="text-sm text-gray-500">Days</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-gray-900">
                    {{ itinerary.summary?.totalActivities }}
                  </div>
                  <div class="text-sm text-gray-500">Activities</div>
                </div>
                <div class="text-center">
                  <div class="text-2xl font-bold text-gray-900">
                    ¥{{ itinerary.summary?.totalEstimatedCost }}
                  </div>
                  <div class="text-sm text-gray-500">Est. Cost</div>
                </div>
              </div>

              <!-- Highlights -->
              <div v-if="itinerary.summary?.highlights?.length" class="mt-6">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Highlights</h4>
                <div class="flex flex-wrap gap-2">
                  <UiBadge
                    v-for="highlight in itinerary.summary.highlights"
                    :key="highlight"
                    variant="success"
                  >
                    {{ highlight }}
                  </UiBadge>
                </div>
              </div>
            </UiCard>

            <!-- Day by day itinerary -->
            <div class="space-y-4">
              <div
                v-for="day in itinerary.dayPlans"
                :key="day.dayNumber"
              >
                <UiCard padding="none">
                  <!-- Day header -->
                  <button
                    class="w-full flex items-center justify-between p-5 hover:bg-gray-50 transition-colors"
                    @click="toggleDay(day.dayNumber)"
                  >
                    <div class="flex items-center gap-4">
                      <div class="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center text-green-600 font-bold">
                        {{ day.dayNumber }}
                      </div>
                      <div class="text-left">
                        <h3 class="font-semibold text-gray-900">Day {{ day.dayNumber }}</h3>
                        <p class="text-sm text-gray-500">{{ formatDayDate(day.date) }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-3">
                      <span class="text-sm text-gray-500">
                        {{ day.activities.length }} activities
                      </span>
                      <ChevronDown
                        :class="[
                          'w-5 h-5 text-gray-400 transition-transform',
                          expandedDays.includes(day.dayNumber) && 'rotate-180'
                        ]"
                      />
                    </div>
                  </button>

                  <!-- Day activities -->
                  <Transition name="expand">
                    <div
                      v-if="expandedDays.includes(day.dayNumber)"
                      class="border-t border-gray-100"
                    >
                      <div class="p-5 space-y-4">
                        <div
                          v-for="activity in day.activities"
                          :key="activity.id"
                          class="flex gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group"
                        >
                          <!-- Time -->
                          <div class="flex-shrink-0 text-center">
                            <div class="text-sm font-medium text-gray-900">
                              {{ activity.startTime }}
                            </div>
                            <div class="text-xs text-gray-500">
                              {{ activity.endTime }}
                            </div>
                          </div>

                          <!-- Content -->
                          <div class="flex-1 min-w-0">
                            <div class="flex items-start justify-between gap-2">
                              <div>
                                <h4 class="font-medium text-gray-900">
                                  {{ activity.name }}
                                </h4>
                                <p class="text-sm text-gray-500 mt-1">
                                  {{ activity.description }}
                                </p>
                              </div>
                              <UiBadge
                                :class="getCategoryColor(activity.category)"
                                size="sm"
                              >
                                {{ activity.category }}
                              </UiBadge>
                            </div>

                            <div class="flex items-center gap-4 mt-3 text-sm text-gray-500">
                              <span class="flex items-center gap-1">
                                <MapPin class="w-4 h-4" />
                                {{ activity.location.name }}
                              </span>
                              <span v-if="activity.cost?.amount" class="flex items-center gap-1">
                                ¥{{ activity.cost.amount }}
                              </span>
                            </div>
                          </div>

                          <!-- Actions -->
                          <div class="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button class="p-2 hover:bg-white rounded-lg text-gray-400 hover:text-gray-600">
                              <GripVertical class="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        <!-- Add activity button -->
                        <button class="w-full py-3 border-2 border-dashed border-gray-200 rounded-xl text-gray-400 hover:border-green-500 hover:text-green-600 transition-colors flex items-center justify-center gap-2">
                          <Plus class="w-4 h-4" />
                          Add Activity
                        </button>

                        <!-- Day notes -->
                        <div
                          v-if="day.notes"
                          class="p-4 bg-amber-50 rounded-xl border border-amber-100"
                        >
                          <p class="text-sm text-amber-800">
                            <strong>Note:</strong> {{ day.notes }}
                          </p>
                        </div>
                      </div>
                    </div>
                  </Transition>
                </UiCard>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}

.expand-enter-to,
.expand-leave-from {
  max-height: 1000px;
}
</style>
