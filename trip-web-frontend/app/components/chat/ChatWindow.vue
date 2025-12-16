<script setup lang="ts">
import { Send, Sparkles, Loader2 } from 'lucide-vue-next'
import type { Message, Conversation } from '~/types'
import { generateId } from '~/utils'

interface Props {
  conversation?: Conversation | null
  fullScreen?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  fullScreen: false,
})

const emit = defineEmits<{
  conversationCreated: [conversation: Conversation]
}>()

const auth = useAuth()
const chat = useChat()

const messages = ref<Message[]>([])
const inputMessage = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const messagesContainer = ref<HTMLDivElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)

// Current conversation (either passed as prop or created)
const currentConversation = ref<Conversation | null>(props.conversation || null)

// Auto-scroll to bottom when new messages arrive
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Watch for message changes
watch(messages, () => scrollToBottom(), { deep: true })
watch(streamingContent, () => scrollToBottom())

// Initialize conversation if prop changes
watch(() => props.conversation, (newConv, oldConv) => {
  // Only load messages if conversation actually changed
  if (newConv?.conversationId !== oldConv?.conversationId) {
    if (newConv) {
      currentConversation.value = newConv
      loadMessages()
    } else {
      // Clear messages when conversation is set to null (new chat)
      currentConversation.value = null
      messages.value = []
    }
  }
}, { immediate: true })

// Load messages for current conversation
const loadMessages = async () => {
  if (!currentConversation.value?.conversationId) {
    messages.value = []
    return
  }
  
  const result = await chat.listMessages(
    auth.userId.value,
    currentConversation.value.conversationId
  )
  
  if (result) {
    messages.value = result.items.reverse()
  }
}

// Create a new conversation if needed
const ensureConversation = async (): Promise<Conversation | null> => {
  if (currentConversation.value) return currentConversation.value
  
  const conversation = await chat.createConversation(
    auth.userId.value,
    'New Chat'
  )
  
  if (conversation) {
    currentConversation.value = conversation
    emit('conversationCreated', conversation)
  }
  
  return conversation
}

// Send message handler
const sendMessage = async () => {
  const content = inputMessage.value.trim()
  if (!content || isStreaming.value) return
  
  // Ensure we have a conversation
  const conversation = await ensureConversation()
  if (!conversation) return
  
  // Add user message locally
  const userMessage: Message = {
    id: generateId(),
    conversationId: conversation.conversationId,
    role: 'user',
    content,
    createdAt: new Date().toISOString(),
  }
  messages.value.push(userMessage)
  inputMessage.value = ''
  
  // Start streaming response
  isStreaming.value = true
  streamingContent.value = ''
  
  try {
    await chat.streamMessage(
      auth.userId.value,
      conversation.conversationId,
      content,
      undefined,
      // onEvent: handle ADK events (tool calls, etc.)
      (event) => {
        console.log('ADK Event:', event)
      },
      // onChunk: accumulate streaming text
      (chunk) => {
        streamingContent.value += chunk
      },
      // onMessage: handle final saved message
      (message) => {
        // Replace streaming content with final message
        streamingContent.value = ''
        messages.value.push(message)
      },
      // onComplete
      () => {
        console.log('Stream completed')
      },
      // onError
      (error) => {
        console.error('Stream error:', error)
        messages.value.push({
          id: generateId(),
          conversationId: conversation.conversationId,
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
          createdAt: new Date().toISOString(),
        })
      }
    )
  } catch (error) {
    console.error('Failed to send message:', error)
    messages.value.push({
      id: generateId(),
      conversationId: conversation.conversationId,
      role: 'assistant',
      content: 'Sorry, I encountered an error. Please try again.',
      createdAt: new Date().toISOString(),
    })
  } finally {
    isStreaming.value = false
    streamingContent.value = ''
  }
}

// Handle enter key
const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

// Auto-resize textarea
const autoResize = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 200) + 'px'
}

// Suggested prompts for new conversations
const suggestedPrompts = [
  { text: 'Plan a weekend trip to Shanghai', icon: '🏙️' },
  { text: 'Find hotels near the Bund', icon: '🏨' },
  { text: 'What are the must-see attractions in Beijing?', icon: '🏛️' },
  { text: 'Create a 3-day itinerary for Hangzhou', icon: '📋' },
]

const useSuggestedPrompt = (prompt: string) => {
  inputMessage.value = prompt
  inputRef.value?.focus()
}
</script>

<template>
  <div
    :class="[
      'flex flex-col bg-white',
      props.fullScreen ? 'h-screen' : 'h-[600px] rounded-2xl shadow-lg border border-gray-100'
    ]"
  >
    <!-- Header -->
    <div class="flex-shrink-0 flex items-center gap-3 px-6 py-4 border-b border-gray-100">
      <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
        <Sparkles class="w-5 h-5 text-white" />
      </div>
      <div>
        <h2 class="font-semibold text-gray-900">AI Travel Assistant</h2>
        <p class="text-sm text-gray-500">Powered by TripSphere</p>
      </div>
    </div>

    <!-- Messages area -->
    <div
      ref="messagesContainer"
      class="flex-1 overflow-y-auto p-6 space-y-4"
    >
      <!-- Empty state with suggestions -->
      <div
        v-if="messages.length === 0 && !isStreaming"
        class="h-full flex flex-col items-center justify-center text-center"
      >
        <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center mb-6 animate-float">
          <Sparkles class="w-10 h-10 text-primary-600" />
        </div>
        <h3 class="text-xl font-semibold text-gray-900 mb-2">
          Welcome to TripSphere AI!
        </h3>
        <p class="text-gray-500 mb-8 max-w-md">
          I'm your intelligent travel assistant. Ask me anything about destinations, hotels, attractions, or let me help you plan your perfect trip.
        </p>
        
        <!-- Suggested prompts -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
          <button
            v-for="prompt in suggestedPrompts"
            :key="prompt.text"
            class="flex items-center gap-3 px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-xl text-left transition-colors"
            @click="useSuggestedPrompt(prompt.text)"
          >
            <span class="text-xl">{{ prompt.icon }}</span>
            <span class="text-sm text-gray-700">{{ prompt.text }}</span>
          </button>
        </div>
      </div>

      <!-- Message list -->
      <template v-for="message in messages" :key="message.id">
        <ChatMessage :message="message" />
      </template>

      <!-- Streaming message -->
      <ChatMessage
        v-if="isStreaming"
        :message="{
          id: 'streaming',
          conversationId: currentConversation?.conversationId || '',
          role: 'assistant',
          content: streamingContent,
          createdAt: new Date().toISOString(),
        }"
        :is-streaming="true"
      />
    </div>

    <!-- Input area -->
    <div class="flex-shrink-0 p-4 border-t border-gray-100">
      <div class="flex items-start gap-3">
        <div class="flex-1 relative">
          <textarea
            ref="inputRef"
            v-model="inputMessage"
            placeholder="Ask me anything about travel..."
            class="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
            rows="1"
            :disabled="isStreaming"
            @keydown="handleKeydown"
            @input="autoResize"
          />
        </div>
        <UiButton
          :disabled="!inputMessage.trim() || isStreaming"
          :loading="isStreaming"
          size="sm"
          class="flex-shrink-0 h-[46px] w-[46px] !p-0"
          @click="sendMessage"
        >
          <Send class="w-5 h-5" />
        </UiButton>
      </div>
      <p class="text-xs text-gray-400 mt-2 text-center">
        Press Enter to send, Shift+Enter for new line
      </p>
    </div>
  </div>
</template>
