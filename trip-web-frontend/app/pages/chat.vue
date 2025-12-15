<script setup lang="ts">
import { Plus, MessageSquare, Trash2, Clock } from 'lucide-vue-next'
import type { Conversation } from '~/types'
import { formatRelativeTime } from '~/utils'

definePageMeta({
  layout: 'default',
})

const auth = useAuth()
const chat = useChat()

const conversations = ref<Conversation[]>([])
const selectedConversation = ref<Conversation | null>(null)
const showSidebar = ref(true)

// Load conversations on mount
onMounted(async () => {
  await loadConversations()
})

const loadConversations = async () => {
  const result = await chat.listConversations(auth.userId.value)
  if (result) {
    conversations.value = result.items
    // Auto-select first conversation if exists
    if (result.items.length > 0 && !selectedConversation.value) {
      selectedConversation.value = result.items[0]
    }
  }
}

const createNewChat = async () => {
  selectedConversation.value = null
}

const selectConversation = (conversation: Conversation) => {
  selectedConversation.value = conversation
}

const handleConversationCreated = (conversation: Conversation) => {
  conversations.value.unshift(conversation)
  selectedConversation.value = conversation
}

const deleteConversation = async (conversation: Conversation) => {
  const success = await chat.deleteConversation(auth.userId.value, conversation.conversationId)
  if (success) {
    conversations.value = conversations.value.filter(c => c.conversationId !== conversation.conversationId)
    if (selectedConversation.value?.conversationId === conversation.conversationId) {
      selectedConversation.value = conversations.value[0] || null
    }
  }
}
</script>

<template>
  <div class="h-[calc(100vh-64px)] flex">
    <!-- Sidebar -->
    <Transition name="slide">
      <aside
        v-if="showSidebar"
        class="w-80 bg-gray-50 border-r border-gray-200 flex flex-col"
      >
        <!-- New chat button -->
        <div class="p-4 border-b border-gray-200">
          <UiButton
            class="w-full justify-center"
            @click="createNewChat"
          >
            <Plus class="w-4 h-4" />
            New Chat
          </UiButton>
        </div>

        <!-- Conversation list -->
        <div class="flex-1 overflow-y-auto">
          <div class="p-2 space-y-1">
            <div
              v-for="conversation in conversations"
              :key="conversation.conversationId"
              :class="[
                'w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors group cursor-pointer',
                selectedConversation?.conversationId === conversation.conversationId
                  ? 'bg-primary-100 text-primary-900'
                  : 'hover:bg-gray-100'
              ]"
              @click="selectConversation(conversation)"
            >
              <MessageSquare class="w-5 h-5 flex-shrink-0 mt-0.5 text-gray-500" />
              <div class="flex-1 min-w-0">
                <p class="font-medium text-sm truncate">
                  {{ conversation.title || 'New Chat' }}
                </p>
                <p class="text-xs text-gray-500 flex items-center gap-1 mt-1">
                  <Clock class="w-3 h-3" />
                  {{ formatRelativeTime(conversation.updatedAt || conversation.createdAt) }}
                </p>
              </div>
              <button
                class="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-100 text-gray-400 hover:text-red-600 transition-all"
                @click.stop="deleteConversation(conversation)"
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Empty state -->
          <div
            v-if="conversations.length === 0"
            class="p-6 text-center"
          >
            <MessageSquare class="w-12 h-12 mx-auto text-gray-300 mb-3" />
            <p class="text-gray-500 text-sm">No conversations yet</p>
            <p class="text-gray-400 text-xs mt-1">Start a new chat to begin</p>
          </div>
        </div>
      </aside>
    </Transition>

    <!-- Main chat area -->
    <main class="flex-1 flex flex-col bg-white">
      <ChatWindow
        :conversation="selectedConversation"
        :full-screen="true"
        @conversation-created="handleConversationCreated"
      />
    </main>
  </div>
</template>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}
</style>
