<script setup lang="ts">
import { 
  FileText, 
  Plus, 
  Search, 
  Filter, 
  Heart, 
  MessageSquare, 
  Eye,
  Clock,
  Edit3,
  Trash2,
  MoreVertical
} from 'lucide-vue-next'
import type { Note } from '~/types'
import { formatRelativeTime } from '~/utils'

definePageMeta({
  layout: 'default',
})

const auth = useAuth()

// Mock notes data
const mockNotes: Note[] = [
  {
    id: '1',
    userId: 'user1',
    title: 'Amazing Weekend in Shanghai',
    content: 'My trip to Shanghai was absolutely incredible! From the historic Bund to the modern Pudong skyline, every moment was memorable. The food was exceptional, especially the xiaolongbao at Din Tai Fung...',
    coverImage: 'https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&h=400&fit=crop',
    tags: ['Shanghai', 'City Trip', 'Food'],
    likes: 245,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
    published: true,
  },
  {
    id: '2',
    userId: 'user2',
    title: 'West Lake: A Photographer\'s Paradise',
    content: 'As a photographer, West Lake in Hangzhou has always been on my bucket list. The misty mornings, traditional pagodas, and serene waters create the perfect backdrop for stunning photos...',
    coverImage: 'https://images.unsplash.com/photo-1591122947157-26bad3a117d2?w=600&h=400&fit=crop',
    tags: ['Hangzhou', 'Photography', 'Nature'],
    likes: 189,
    createdAt: '2024-01-14T15:30:00Z',
    updatedAt: '2024-01-14T15:30:00Z',
    published: true,
  },
  {
    id: '3',
    userId: 'user3',
    title: 'Hidden Gems of Beijing Hutongs',
    content: 'Wandering through Beijing\'s ancient hutongs was like stepping back in time. The narrow alleyways are filled with history, local eateries, and charming courtyard homes that tell stories of old Beijing...',
    coverImage: 'https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600&h=400&fit=crop',
    tags: ['Beijing', 'Culture', 'History'],
    likes: 312,
    createdAt: '2024-01-13T09:15:00Z',
    updatedAt: '2024-01-13T09:15:00Z',
    published: true,
  },
  {
    id: '4',
    userId: 'user1',
    title: 'A Foodie\'s Guide to Chengdu',
    content: 'If you love spicy food, Chengdu is your paradise! From mouth-numbing hotpot to delicious street snacks, the capital of Sichuan province offers an unforgettable culinary adventure...',
    coverImage: 'https://images.unsplash.com/photo-1552566626-52f8b828add9?w=600&h=400&fit=crop',
    tags: ['Chengdu', 'Food', 'Sichuan'],
    likes: 278,
    createdAt: '2024-01-12T14:45:00Z',
    updatedAt: '2024-01-12T14:45:00Z',
    published: true,
  },
  {
    id: '5',
    userId: 'user4',
    title: 'Suzhou: Venice of the East',
    content: 'The classical gardens of Suzhou are UNESCO World Heritage sites for a reason. Walking through the Humble Administrator\'s Garden, I felt transported to an ancient Chinese painting...',
    coverImage: 'https://images.unsplash.com/photo-1528164344705-47542687000d?w=600&h=400&fit=crop',
    tags: ['Suzhou', 'Gardens', 'UNESCO'],
    likes: 156,
    createdAt: '2024-01-11T11:20:00Z',
    updatedAt: '2024-01-11T11:20:00Z',
    published: true,
  },
  {
    id: '6',
    userId: 'user5',
    title: 'Night Markets of Taiwan',
    content: 'Taiwan\'s night markets are a sensory overload in the best way possible. From stinky tofu to bubble tea, oyster omelets to mochi, there\'s something for every adventurous eater...',
    coverImage: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&h=400&fit=crop',
    tags: ['Taiwan', 'Night Market', 'Street Food'],
    likes: 423,
    createdAt: '2024-01-10T20:00:00Z',
    updatedAt: '2024-01-10T20:00:00Z',
    published: true,
  },
]

// User's own notes
const myNotes = computed(() => {
  return mockNotes.filter(n => n.userId === auth.userId.value).slice(0, 2)
})

const searchQuery = ref('')
const selectedTag = ref<string | null>(null)

// Get all unique tags
const allTags = computed(() => {
  const tags = new Set<string>()
  mockNotes.forEach(note => {
    note.tags?.forEach(tag => tags.add(tag))
  })
  return Array.from(tags).slice(0, 10)
})

const filteredNotes = computed(() => {
  let result = mockNotes

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(
      n => n.title.toLowerCase().includes(query) ||
           n.content.toLowerCase().includes(query) ||
           n.tags?.some(t => t.toLowerCase().includes(query))
    )
  }

  if (selectedTag.value) {
    result = result.filter(n => n.tags?.includes(selectedTag.value!))
  }

  return result
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Hero section -->
    <div class="bg-gradient-to-br from-amber-500 to-orange-500 text-white py-16">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center animate-fade-in-up">
          <h1 class="text-4xl sm:text-5xl font-bold mb-4">Travel Stories</h1>
          <p class="text-xl text-white/80 max-w-2xl mx-auto mb-8">
            Share your adventures and discover inspiring travel stories from fellow explorers.
          </p>
          
          <!-- Search bar -->
          <div class="max-w-2xl mx-auto flex gap-3">
            <div class="relative flex-1">
              <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                v-model="searchQuery"
                type="text"
                placeholder="Search travel stories..."
                class="w-full pl-12 pr-4 py-4 rounded-xl text-gray-900 bg-white shadow-lg focus:outline-none focus:ring-4 focus:ring-white/30 transition-all"
              />
            </div>
            <NuxtLink
              to="/notes/new"
              class="flex items-center gap-2 px-6 py-4 bg-white text-amber-600 rounded-xl font-semibold hover:shadow-lg transition-all"
            >
              <Plus class="w-5 h-5" />
              Write
            </NuxtLink>
          </div>
        </div>
      </div>
    </div>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- My Notes section -->
      <section v-if="myNotes.length > 0" class="mb-12">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-2xl font-bold text-gray-900">My Notes</h2>
          <NuxtLink
            to="/notes/my"
            class="text-primary-600 hover:text-primary-700 font-medium text-sm flex items-center gap-1"
          >
            View All
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </NuxtLink>
        </div>

        <div class="grid sm:grid-cols-2 gap-6">
          <div
            v-for="note in myNotes"
            :key="note.id"
            class="animate-fade-in-up"
          >
            <UiCard padding="none" hover>
              <div class="flex">
                <!-- Image -->
                <div class="w-1/3 aspect-square">
                  <img
                    :src="note.coverImage"
                    :alt="note.title"
                    class="w-full h-full object-cover rounded-l-xl"
                  />
                </div>
                <!-- Content -->
                <div class="flex-1 p-4 flex flex-col">
                  <h3 class="font-semibold text-gray-900 line-clamp-1 mb-2">
                    {{ note.title }}
                  </h3>
                  <p class="text-sm text-gray-500 line-clamp-2 flex-1">
                    {{ note.content }}
                  </p>
                  <div class="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                    <span class="text-xs text-gray-400">
                      {{ formatRelativeTime(note.updatedAt) }}
                    </span>
                    <div class="flex gap-2">
                      <NuxtLink
                        :to="`/notes/${note.id}/edit`"
                        class="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                      >
                        <Edit3 class="w-4 h-4" />
                      </NuxtLink>
                      <button class="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600">
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </UiCard>
          </div>
        </div>
      </section>

      <!-- Tags filter -->
      <div class="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
        <button
          :class="[
            'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
            !selectedTag
              ? 'bg-amber-500 text-white shadow-md'
              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
          ]"
          @click="selectedTag = null"
        >
          All
        </button>
        <button
          v-for="tag in allTags"
          :key="tag"
          :class="[
            'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
            selectedTag === tag
              ? 'bg-amber-500 text-white shadow-md'
              : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
          ]"
          @click="selectedTag = tag"
        >
          {{ tag }}
        </button>
      </div>

      <!-- Results count -->
      <p class="text-gray-600 mb-6">
        {{ filteredNotes.length }} stories found
      </p>

      <!-- Notes grid -->
      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <NuxtLink
          v-for="(note, index) in filteredNotes"
          :key="note.id"
          :to="`/notes/${note.id}`"
          class="group animate-fade-in-up"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <UiCard padding="none" hover clickable>
            <!-- Cover image -->
            <div class="relative aspect-[4/3] overflow-hidden rounded-t-xl">
              <img
                :src="note.coverImage"
                :alt="note.title"
                class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
              />
              <!-- Gradient overlay -->
              <div class="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
              <!-- Tags -->
              <div class="absolute bottom-3 left-3 flex gap-2">
                <UiBadge
                  v-for="tag in note.tags?.slice(0, 2)"
                  :key="tag"
                  class="bg-white/90 text-gray-700"
                  size="sm"
                >
                  {{ tag }}
                </UiBadge>
              </div>
            </div>

            <!-- Content -->
            <div class="p-5">
              <!-- Title -->
              <h3 class="text-lg font-semibold text-gray-900 group-hover:text-amber-600 transition-colors line-clamp-2 mb-2">
                {{ note.title }}
              </h3>

              <!-- Excerpt -->
              <p class="text-gray-500 text-sm line-clamp-2 mb-4">
                {{ note.content }}
              </p>

              <!-- Footer -->
              <div class="flex items-center justify-between pt-4 border-t border-gray-100">
                <div class="flex items-center gap-1 text-sm text-gray-400">
                  <Clock class="w-4 h-4" />
                  {{ formatRelativeTime(note.createdAt) }}
                </div>
                <div class="flex items-center gap-4">
                  <span class="flex items-center gap-1 text-sm text-gray-500">
                    <Heart class="w-4 h-4" />
                    {{ note.likes }}
                  </span>
                </div>
              </div>
            </div>
          </UiCard>
        </NuxtLink>
      </div>

      <!-- Empty state -->
      <div
        v-if="filteredNotes.length === 0"
        class="text-center py-16"
      >
        <FileText class="w-16 h-16 mx-auto text-gray-300 mb-4" />
        <h3 class="text-xl font-semibold text-gray-900 mb-2">No stories found</h3>
        <p class="text-gray-500 mb-6">Try adjusting your search or filters</p>
        <NuxtLink
          to="/notes/new"
          class="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 text-white rounded-lg font-medium hover:bg-amber-600 transition-colors"
        >
          <Plus class="w-5 h-5" />
          Write Your Story
        </NuxtLink>
      </div>
    </div>
  </div>
</template>
