<script setup lang="ts">
import { MapPin, Star, Clock, Ticket, Search, Filter, ChevronDown, Heart, Eye } from 'lucide-vue-next'
import type { Attraction } from '~/types'

definePageMeta({
  layout: 'default',
})

// Mock data for attractions
const mockAttractions: Attraction[] = [
  {
    id: '1',
    name: 'The Bund',
    description: 'A waterfront area in central Shanghai featuring a mix of historical buildings and modern skyscrapers.',
    address: { country: 'China', province: 'Shanghai', city: 'Shanghai', county: 'Huangpu', district: '', street: 'Zhongshan East 1st Road' },
    location: { lng: 121.4883, lat: 31.2319 },
    category: 'Landmark',
    rating: 4.8,
    openingHours: '24 hours',
    ticketPrice: 'Free',
    images: ['https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&h=400&fit=crop'],
    tags: ['Historic', 'Scenic', 'Night View'],
  },
  {
    id: '2',
    name: 'Yu Garden',
    description: 'A classical Chinese garden located in the Old City of Shanghai, featuring traditional architecture and landscapes.',
    address: { country: 'China', province: 'Shanghai', city: 'Shanghai', county: 'Huangpu', district: '', street: 'Anren Street' },
    location: { lng: 121.4920, lat: 31.2270 },
    category: 'Garden',
    rating: 4.6,
    openingHours: '8:30 AM - 5:00 PM',
    ticketPrice: '¥40',
    images: ['https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=600&h=400&fit=crop'],
    tags: ['Traditional', 'Cultural', 'Architecture'],
  },
  {
    id: '3',
    name: 'Shanghai Tower',
    description: 'The tallest building in China and second-tallest in the world, featuring an observation deck with stunning views.',
    address: { country: 'China', province: 'Shanghai', city: 'Shanghai', county: 'Pudong', district: '', street: 'Lujiazui Ring Road' },
    location: { lng: 121.5055, lat: 31.2335 },
    category: 'Architecture',
    rating: 4.7,
    openingHours: '8:30 AM - 9:30 PM',
    ticketPrice: '¥180',
    images: ['https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=600&h=400&fit=crop'],
    tags: ['Modern', 'Skyscraper', 'Observation'],
  },
  {
    id: '4',
    name: 'Oriental Pearl Tower',
    description: 'An iconic TV tower and landmark of Shanghai with multiple observation decks and entertainment facilities.',
    address: { country: 'China', province: 'Shanghai', city: 'Shanghai', county: 'Pudong', district: '', street: 'Century Avenue' },
    location: { lng: 121.4956, lat: 31.2397 },
    category: 'Landmark',
    rating: 4.5,
    openingHours: '8:00 AM - 9:30 PM',
    ticketPrice: '¥220',
    images: ['https://images.unsplash.com/photo-1545893835-abaa50cbe628?w=600&h=400&fit=crop'],
    tags: ['Iconic', 'Tower', 'Entertainment'],
  },
  {
    id: '5',
    name: 'West Lake',
    description: 'A UNESCO World Heritage Site, this freshwater lake is surrounded by mountains and offers beautiful scenery.',
    address: { country: 'China', province: 'Zhejiang', city: 'Hangzhou', county: '', district: '', street: '' },
    location: { lng: 120.1485, lat: 30.2421 },
    category: 'Nature',
    rating: 4.9,
    openingHours: '24 hours',
    ticketPrice: 'Free',
    images: ['https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=600&h=400&fit=crop'],
    tags: ['UNESCO', 'Lake', 'Scenic'],
  },
  {
    id: '6',
    name: 'Forbidden City',
    description: 'The former Chinese imperial palace and now a palace museum, featuring traditional Chinese palatial architecture.',
    address: { country: 'China', province: 'Beijing', city: 'Beijing', county: 'Dongcheng', district: '', street: '' },
    location: { lng: 116.3972, lat: 39.9169 },
    category: 'Museum',
    rating: 4.8,
    openingHours: '8:30 AM - 5:00 PM',
    ticketPrice: '¥60',
    images: ['https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600&h=400&fit=crop'],
    tags: ['Imperial', 'Historic', 'UNESCO'],
  },
]

const searchQuery = ref('')
const selectedCategory = ref<string | null>(null)
const showFilters = ref(false)

const categories = ['All', 'Landmark', 'Garden', 'Architecture', 'Nature', 'Museum']

const filteredAttractions = computed(() => {
  let result = mockAttractions

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(
      a => a.name.toLowerCase().includes(query) ||
           a.description.toLowerCase().includes(query) ||
           a.tags?.some(t => t.toLowerCase().includes(query))
    )
  }

  if (selectedCategory.value && selectedCategory.value !== 'All') {
    result = result.filter(a => a.category === selectedCategory.value)
  }

  return result
})

const selectCategory = (category: string) => {
  selectedCategory.value = category === 'All' ? null : category
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Hero section -->
    <div class="bg-gradient-to-br from-primary-600 to-secondary-600 text-white py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center animate-fade-in-up">
          <h1 class="text-4xl sm:text-5xl font-bold mb-4">Discover Amazing Attractions</h1>
          <p class="text-xl text-white/80 max-w-2xl mx-auto mb-8">
            Explore the world's most incredible destinations and find your next adventure.
          </p>
          
          <!-- Search bar -->
          <div class="max-w-2xl mx-auto">
            <div class="relative">
              <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search attractions, cities, or categories..."
                class="w-full pl-12 pr-4 py-4 rounded-xl text-gray-900 bg-white shadow-lg focus:outline-none focus:ring-4 focus:ring-white/30 transition-all"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Filters -->
      <div class="flex items-center justify-between mb-8">
        <!-- Categories -->
        <div class="flex items-center gap-2 overflow-x-auto pb-2">
          <button
            v-for="category in categories"
            :key="category"
            :class="[
              'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
              (category === 'All' && !selectedCategory) || selectedCategory === category
                ? 'bg-primary-600 text-white shadow-md'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
            ]"
            @click="selectCategory(category)"
          >
            {{ category }}
          </button>
        </div>

        <!-- Filter button -->
        <button
          class="flex items-center gap-2 px-4 py-2 bg-white rounded-lg text-gray-700 border border-gray-200 hover:bg-gray-50 transition-colors"
          @click="showFilters = !showFilters"
        >
          <Filter class="w-4 h-4" />
          Filters
          <ChevronDown :class="['w-4 h-4 transition-transform', showFilters && 'rotate-180']" />
        </button>
      </div>

      <!-- Results count -->
      <p class="text-gray-600 mb-6">
        {{ filteredAttractions.length }} attractions found
      </p>

      <!-- Attractions grid -->
      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <NuxtLink
          v-for="(attraction, index) in filteredAttractions"
          :key="attraction.id"
          :to="`/attractions/${attraction.id}`"
          class="group animate-fade-in-up"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <UiCard padding="none" hover clickable>
            <!-- Image -->
            <div class="relative aspect-[4/3] overflow-hidden rounded-t-xl">
              <img
                :src="attraction.images?.[0]"
                :alt="attraction.name"
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              />
              <!-- Overlay badges -->
              <div class="absolute top-3 left-3 flex gap-2">
                <UiBadge variant="default" size="sm">
                  {{ attraction.category }}
                </UiBadge>
              </div>
              <!-- Like button -->
              <button
                class="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/90 flex items-center justify-center text-gray-600 hover:text-red-500 hover:bg-white transition-all"
                @click.prevent
              >
                <Heart class="w-5 h-5" />
              </button>
            </div>

            <!-- Content -->
            <div class="p-5">
              <!-- Title and rating -->
              <div class="flex items-start justify-between gap-2 mb-2">
                <h3 class="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                  {{ attraction.name }}
                </h3>
                <div class="flex items-center gap-1 text-amber-500">
                  <Star class="w-4 h-4 fill-current" />
                  <span class="text-sm font-medium text-gray-700">{{ attraction.rating }}</span>
                </div>
              </div>

              <!-- Location -->
              <p class="flex items-center gap-1 text-sm text-gray-500 mb-3">
                <MapPin class="w-4 h-4" />
                {{ attraction.address.city }}, {{ attraction.address.country }}
              </p>

              <!-- Description -->
              <p class="text-gray-600 text-sm line-clamp-2 mb-4">
                {{ attraction.description }}
              </p>

              <!-- Tags -->
              <div class="flex flex-wrap gap-2 mb-4">
                <UiBadge
                  v-for="tag in attraction.tags?.slice(0, 3)"
                  :key="tag"
                  variant="secondary"
                  size="sm"
                >
                  {{ tag }}
                </UiBadge>
              </div>

              <!-- Footer info -->
              <div class="flex items-center justify-between pt-4 border-t border-gray-100">
                <div class="flex items-center gap-1 text-sm text-gray-500">
                  <Clock class="w-4 h-4" />
                  {{ attraction.openingHours }}
                </div>
                <div class="flex items-center gap-1 text-sm font-medium text-primary-600">
                  <Ticket class="w-4 h-4" />
                  {{ attraction.ticketPrice }}
                </div>
              </div>
            </div>
          </UiCard>
        </NuxtLink>
      </div>

      <!-- Empty state -->
      <div
        v-if="filteredAttractions.length === 0"
        class="text-center py-16"
      >
        <MapPin class="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 mb-2">No attractions found</h3>
        <p class="text-gray-500">Try adjusting your search or filters</p>
      </div>
    </div>
  </div>
</template>
