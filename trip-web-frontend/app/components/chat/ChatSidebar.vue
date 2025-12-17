<script setup lang="ts">
import { X, Send, Sparkles, Loader2 } from 'lucide-vue-next'
import type { Message, Conversation, ChatContext } from '~/types'
import { generateId } from '~/utils'

interface Props {
  isOpen: boolean
  conversation?: Conversation | null
  initialContext?: ChatContext | null
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  isOpen: false,
  title: 'AI Assistant',
})

const emit = defineEmits<{
  close: []
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
watch(() => props.conversation, (newConv) => {
  if (newConv) {
    currentConversation.value = newConv
    loadMessages()
  }
})

// When sidebar opens with initial context, create conversation
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen && props.initialContext && !currentConversation.value) {
    await createContextualConversation()
    
    // After creating conversation, check if we need to auto-send a query
    if (props.initialContext.autoSendQuery && currentConversation.value) {
      // Wait a moment for UI to settle
      await nextTick()
      inputMessage.value = props.initialContext.autoSendQuery
      // Use autoSendMetadata if provided
      const metadata = props.initialContext.autoSendMetadata || props.initialContext
      await sendMessageWithMetadata(metadata)
    }
  }
})

// Load messages for current conversation
const loadMessages = async () => {
  if (!currentConversation.value) return
  
  const result = await chat.listMessages(
    auth.userId.value,
    currentConversation.value.conversationId
  )
  
  if (result) {
    messages.value = result.items.reverse()
  }
}

// Create a conversation with initial context
const createContextualConversation = async () => {
  if (!props.initialContext) return
  
  const conversation = await chat.createConversation(
    auth.userId.value,
    props.title,
    props.initialContext
  )
  
  if (conversation) {
    currentConversation.value = conversation
    emit('conversationCreated', conversation)
  }
}

// Create a new conversation if needed
const ensureConversation = async (): Promise<Conversation | null> => {
  if (currentConversation.value) return currentConversation.value
  
  const conversation = await chat.createConversation(
    auth.userId.value,
    props.title || 'New Chat'
  )
  
  if (conversation) {
    currentConversation.value = conversation
    emit('conversationCreated', conversation)
  }
  
  return conversation
}

// Send message handler with optional custom metadata
const sendMessageWithMetadata = async (customMetadata?: Record<string, unknown>) => {
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
  
  // Use custom metadata if provided, otherwise use initialContext
  const metadata = customMetadata || props.initialContext || undefined
  
  try {
    await chat.streamMessage(
      auth.userId.value,
      conversation.conversationId,
      content,
      metadata,
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

// Send message handler (uses default metadata from initialContext)
const sendMessage = async () => {
  await sendMessageWithMetadata()
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
  target.style.height = Math.min(target.scrollHeight, 120) + 'px'
}

// Reset state when closing
const handleClose = () => {
  // Reset conversation state to allow creating a new one next time
  currentConversation.value = null
  messages.value = []
  inputMessage.value = ''
  streamingContent.value = ''
  emit('close')
}

// Quick prompts for review context
const quickPrompts = computed(() => {
  if (props.initialContext?.type === 'review-summary') {
    return [
      'Summarize the reviews',
      'What do visitors like most?',
      'Any negative feedback?',
      'Best time to visit?',
    ]
  }
  return [
    'Tell me more',
    'How to get there?',
    'Nearby attractions',
    'Local tips',
  ]
})

const useQuickPrompt = (prompt: string) => {
  inputMessage.value = prompt
  sendMessage()
}
</script>

<template>
  <!-- Backdrop (only on mobile) -->
  <Transition name="fade">
    <div
      v-if="isOpen"
      class="fixed inset-0 bg-black/20 z-40 lg:hidden"
      @click="handleClose"
    />
  </Transition>

  <!-- Sidebar -->
  <Transition name="slide">
    <div
      v-if="isOpen"
      class="fixed right-0 top-16 bottom-0 w-full sm:w-[400px] lg:w-[420px] bg-white shadow-2xl z-40 flex flex-col border-l border-gray-200"
    >
      <!-- Header -->
      <div class="flex-shrink-0 flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gradient-to-r from-primary-50 to-secondary-50">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
            <Sparkles class="w-4 h-4 text-white" />
          </div>
          <div>
            <h2 class="font-semibold text-gray-900 text-sm">{{ title }}</h2>
            <p class="text-xs text-gray-500">AI Travel Assistant</p>
          </div>
        </div>
        <button
          class="w-8 h-8 rounded-lg hover:bg-gray-100 flex items-center justify-center text-gray-500 hover:text-gray-700 transition-colors"
          @click="handleClose"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Messages area -->
      <div
        ref="messagesContainer"
        class="flex-1 overflow-y-auto p-4 space-y-4"
      >
        <!-- Empty state -->
        <div
          v-if="messages.length === 0 && !isStreaming"
          class="h-full flex flex-col items-center justify-center text-center px-4"
        >
          <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center mb-4">
            <Sparkles class="w-8 h-8 text-primary-600" />
          </div>
          <p class="text-sm text-gray-500 mb-4">
            Ask me anything about this attraction or the reviews!
          </p>
          
          <!-- Quick prompts -->
          <div class="flex flex-wrap gap-2 justify-center">
            <button
              v-for="prompt in quickPrompts"
              :key="prompt"
              class="px-3 py-1.5 text-xs bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
              @click="useQuickPrompt(prompt)"
            >
              {{ prompt }}
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

      <!-- Quick prompts when conversation is active -->
      <div v-if="messages.length > 0" class="flex-shrink-0 px-4 py-2 border-t border-gray-100 bg-gray-50">
        <div class="flex gap-2 overflow-x-auto pb-1">
          <button
            v-for="prompt in quickPrompts"
            :key="prompt"
            class="flex-shrink-0 px-3 py-1 text-xs bg-white border border-gray-200 hover:border-primary-300 hover:bg-primary-50 rounded-full text-gray-600 transition-colors"
            @click="useQuickPrompt(prompt)"
          >
            {{ prompt }}
          </button>
        </div>
      </div>

      <!-- Input area -->
      <div class="flex-shrink-0 p-4 border-t border-gray-100 bg-white">
        <div class="flex items-start gap-2">
          <div class="flex-1 relative">
            <textarea
              ref="inputRef"
              v-model="inputMessage"
              placeholder="Type your question..."
              class="w-full px-3 py-2.5 bg-gray-50 border border-gray-200 rounded-xl resize-none text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
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
            class="flex-shrink-0 h-10 w-10 !p-0"
            @click="sendMessage"
          >
            <Send class="w-4 h-4" />
          </UiButton>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
