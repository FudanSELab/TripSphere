<script setup lang="ts">
import { MapPin, Hotel, Calendar, MessageSquare, FileText, User, LogOut, Menu, X } from 'lucide-vue-next'

const auth = useAuth()
const route = useRoute()
const isMobileMenuOpen = ref(false)

const navLinks = [
  { name: 'Attractions', path: '/attractions', icon: MapPin },
  { name: 'Hotels', path: '/hotels', icon: Hotel },
  { name: 'Itinerary', path: '/itinerary', icon: Calendar },
  { name: 'Notes', path: '/notes', icon: FileText },
]

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}

const handleLogout = () => {
  auth.logout()
  navigateTo('/')
}
</script>

<template>
  <header class="fixed top-0 left-0 right-0 z-40 glass">
    <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <NuxtLink to="/" class="flex items-center gap-2 group">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-xl shadow-lg group-hover:scale-105 transition-transform">
            T
          </div>
          <span class="text-xl font-bold gradient-text hidden sm:inline">TripSphere</span>
        </NuxtLink>

        <!-- Desktop Navigation -->
        <div class="hidden md:flex items-center gap-1">
          <NuxtLink
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            :class="[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200',
              isActive(link.path)
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
            ]"
          >
            <component :is="link.icon" class="w-4 h-4" />
            {{ link.name }}
          </NuxtLink>
        </div>

        <!-- Right side actions -->
        <div class="flex items-center gap-3">
          <!-- Chat button -->
          <NuxtLink
            to="/chat"
            class="hidden sm:flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary-500 to-secondary-500 text-white rounded-lg text-sm font-medium hover:shadow-lg hover:scale-105 transition-all duration-200"
          >
            <MessageSquare class="w-4 h-4" />
            AI Assistant
          </NuxtLink>

          <!-- User menu -->
          <div v-if="auth.isAuthenticated.value" class="relative group">
            <button class="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
              <UiAvatar
                :name="auth.currentUser.value?.username"
                size="sm"
              />
              <span class="hidden sm:inline text-sm font-medium text-gray-700">
                {{ auth.currentUser.value?.username }}
              </span>
            </button>
            
            <!-- Dropdown -->
            <div class="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
              <div class="p-2">
                <NuxtLink
                  to="/profile"
                  class="flex items-center gap-3 px-3 py-2 text-sm text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <User class="w-4 h-4" />
                  Profile
                </NuxtLink>
                <button
                  class="flex items-center gap-3 w-full px-3 py-2 text-sm text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                  @click="handleLogout"
                >
                  <LogOut class="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          </div>
          <div v-else class="flex items-center gap-2">
            <NuxtLink
              to="/login"
              class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors"
            >
              Login
            </NuxtLink>
            <NuxtLink
              to="/register"
              class="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
            >
              Sign Up
            </NuxtLink>
          </div>

          <!-- Mobile menu button -->
          <button
            class="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            @click="isMobileMenuOpen = !isMobileMenuOpen"
          >
            <Menu v-if="!isMobileMenuOpen" class="w-5 h-5 text-gray-700" />
            <X v-else class="w-5 h-5 text-gray-700" />
          </button>
        </div>
      </div>
    </nav>

    <!-- Mobile Navigation -->
    <Transition name="slide-down">
      <div
        v-if="isMobileMenuOpen"
        class="md:hidden bg-white border-t border-gray-100"
      >
        <div class="px-4 py-3 space-y-1">
          <NuxtLink
            v-for="link in navLinks"
            :key="link.path"
            :to="link.path"
            :class="[
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
              isActive(link.path)
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            ]"
            @click="isMobileMenuOpen = false"
          >
            <component :is="link.icon" class="w-5 h-5" />
            {{ link.name }}
          </NuxtLink>
          <NuxtLink
            to="/chat"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium bg-gradient-to-r from-primary-500 to-secondary-500 text-white"
            @click="isMobileMenuOpen = false"
          >
            <MessageSquare class="w-5 h-5" />
            AI Assistant
          </NuxtLink>
        </div>
      </div>
    </Transition>
  </header>
</template>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter-from,
.slide-down-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
