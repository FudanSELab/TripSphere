// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],

  css: ['~/assets/css/main.css'],

  tailwindcss: {
    cssPath: '~/assets/css/tailwind.css',
  },

  app: {
    head: {
      title: 'TripSphere - AI Travel Assistant',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { 
          name: 'description', 
          content: 'TripSphere is an intelligent travel planning platform powered by AI. Discover attractions, plan itineraries, and create travel memories with our smart assistant.' 
        },
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ],
    },
    pageTransition: { name: 'page', mode: 'out-in' },
    layoutTransition: { name: 'layout', mode: 'out-in' },
  },

  runtimeConfig: {
    public: {
      chatServiceUrl: process.env.NUXT_PUBLIC_CHAT_SERVICE_URL || 'http://localhost:8000',
      hotelServiceUrl: process.env.NUXT_PUBLIC_HOTEL_SERVICE_URL || 'http://localhost:8001',
      attractionServiceUrl: process.env.NUXT_PUBLIC_ATTRACTION_SERVICE_URL || 'http://localhost:8002',
      itineraryServiceUrl: process.env.NUXT_PUBLIC_ITINERARY_SERVICE_URL || 'http://localhost:8003',
      noteServiceUrl: process.env.NUXT_PUBLIC_NOTE_SERVICE_URL || 'http://localhost:8004',
      fileServiceUrl: process.env.NUXT_PUBLIC_FILE_SERVICE_URL || 'http://localhost:8005',
    },
  },

  typescript: {
    strict: true,
    shim: false,
  },
})
