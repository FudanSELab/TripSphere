<script setup lang="ts">
import ChatSidebar from '~/components/chat/ChatSidebar.vue'

const auth = useAuth()
const chatSidebar = useChatSidebar()

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
    
    <!-- Global Chat Sidebar -->
    <ChatSidebar
      :is-open="chatSidebar.isChatSidebarOpen.value"
      :initial-context="chatSidebar.chatContext.value"
      :title="chatSidebar.chatTitle.value"
      @close="chatSidebar.closeChatSidebar"
    />
  </div>
</template>
