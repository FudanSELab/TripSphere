<script setup lang="ts">
// Initialize auth state on app mount
const auth = useAuth()

onMounted(() => {
  auth.initAuth()
})
</script>

<template>
  <div>
    <NuxtRouteAnnouncer />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </div>
</template>
