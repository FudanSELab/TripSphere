<script setup lang="ts">
const auth = useAuth()

// Initialize auth on client side
onMounted(() => {
  auth.initAuth()
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gray-50">
    <LayoutAppHeader />
    <main class="flex-1 pt-16">
      <slot />
    </main>
    <LayoutAppFooter />
  </div>
</template>
