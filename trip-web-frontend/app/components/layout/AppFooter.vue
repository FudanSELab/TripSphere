<script setup lang="ts">
import { MapPin, Mail, Twitter, Github, Heart } from 'lucide-vue-next'

const currentYear = new Date().getFullYear()

const footerLinks = {
  product: [
    { name: 'Features', href: '#features' },
    { name: 'Attractions', href: '/attractions' },
    { name: 'Hotels', href: '/hotels' },
    { name: 'Itinerary Planner', href: '/itinerary' },
  ],
  resources: [
    { name: 'Documentation', href: '#' },
    { name: 'API Reference', href: '#' },
    { name: 'Travel Guides', href: '#' },
    { name: 'Blog', href: '#' },
  ],
  company: [
    { name: 'About Us', href: '#' },
    { name: 'Careers', href: '#' },
    { name: 'Contact', href: '#' },
    { name: 'Press', href: '#' },
  ],
  legal: [
    { name: 'Privacy Policy', href: '#' },
    { name: 'Terms of Service', href: '#' },
    { name: 'Cookie Policy', href: '#' },
  ],
}

const socialLinks = [
  { name: 'Twitter', icon: Twitter, href: '#' },
  { name: 'GitHub', icon: Github, href: '#' },
  { name: 'Email', icon: Mail, href: 'mailto:contact@tripsphere.com' },
]
</script>

<template>
  <footer class="bg-gray-900 text-gray-300">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
      <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8 lg:gap-12">
        <!-- Brand -->
        <div class="col-span-2 lg:col-span-1">
          <NuxtLink to="/" class="flex items-center gap-2">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-xl">
              T
            </div>
            <span class="text-xl font-bold text-white">TripSphere</span>
          </NuxtLink>
          <p class="mt-4 text-sm text-gray-400 max-w-xs">
            Your intelligent travel companion. Plan, explore, and create unforgettable memories with AI-powered assistance.
          </p>
          <div class="flex items-center gap-4 mt-6">
            <a
              v-for="social in socialLinks"
              :key="social.name"
              :href="social.href"
              class="w-10 h-10 rounded-lg bg-gray-800 flex items-center justify-center text-gray-400 hover:bg-primary-600 hover:text-white transition-all duration-200"
              :title="social.name"
            >
              <component :is="social.icon" class="w-5 h-5" />
            </a>
          </div>
        </div>

        <!-- Product Links -->
        <div>
          <h3 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">
            Product
          </h3>
          <ul class="space-y-3">
            <li v-for="link in footerLinks.product" :key="link.name">
              <NuxtLink
                :to="link.href"
                class="text-sm text-gray-400 hover:text-white transition-colors"
              >
                {{ link.name }}
              </NuxtLink>
            </li>
          </ul>
        </div>

        <!-- Resources Links -->
        <div>
          <h3 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">
            Resources
          </h3>
          <ul class="space-y-3">
            <li v-for="link in footerLinks.resources" :key="link.name">
              <a
                :href="link.href"
                class="text-sm text-gray-400 hover:text-white transition-colors"
              >
                {{ link.name }}
              </a>
            </li>
          </ul>
        </div>

        <!-- Company Links -->
        <div>
          <h3 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">
            Company
          </h3>
          <ul class="space-y-3">
            <li v-for="link in footerLinks.company" :key="link.name">
              <a
                :href="link.href"
                class="text-sm text-gray-400 hover:text-white transition-colors"
              >
                {{ link.name }}
              </a>
            </li>
          </ul>
        </div>

        <!-- Legal Links -->
        <div>
          <h3 class="text-sm font-semibold text-white uppercase tracking-wider mb-4">
            Legal
          </h3>
          <ul class="space-y-3">
            <li v-for="link in footerLinks.legal" :key="link.name">
              <a
                :href="link.href"
                class="text-sm text-gray-400 hover:text-white transition-colors"
              >
                {{ link.name }}
              </a>
            </li>
          </ul>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="mt-12 pt-8 border-t border-gray-800">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <p class="text-sm text-gray-400">
            &copy; {{ currentYear }} TripSphere. All rights reserved.
          </p>
          <p class="text-sm text-gray-400 flex items-center gap-1">
            Made with <Heart class="w-4 h-4 text-red-500 fill-red-500" /> by the TripSphere Team
          </p>
        </div>
      </div>
    </div>
  </footer>
</template>
