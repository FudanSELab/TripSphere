<script setup lang="ts">
import { User, Bot } from 'lucide-vue-next'
import type { Message } from '~/types'
import { formatRelativeTime, cn } from '~/utils'

interface Props {
  message: Message
  isStreaming?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isStreaming: false,
})

const isUser = computed(() => props.message.role === 'user')
</script>

<template>
  <div
    :class="cn(
      'flex gap-3 animate-fade-in-up',
      isUser ? 'flex-row-reverse' : ''
    )"
  >
    <!-- Avatar -->
    <div
      :class="cn(
        'flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center',
        isUser
          ? 'bg-primary-600'
          : 'bg-gradient-to-br from-secondary-500 to-accent-500'
      )"
    >
      <User v-if="isUser" class="w-5 h-5 text-white" />
      <Bot v-else class="w-5 h-5 text-white" />
    </div>

    <!-- Message content -->
    <div
      :class="cn(
        'max-w-[75%] rounded-2xl px-4 py-3',
        isUser
          ? 'bg-primary-600 text-white rounded-tr-none'
          : 'bg-gray-100 text-gray-900 rounded-tl-none'
      )"
    >
      <!-- Message text -->
      <div class="text-sm leading-relaxed whitespace-pre-wrap">
        {{ props.message.content }}
        <!-- Typing indicator for streaming -->
        <span
          v-if="props.isStreaming && !props.message.content"
          class="typing-indicator inline-flex"
        >
          <span></span>
          <span></span>
          <span></span>
        </span>
        <span
          v-else-if="props.isStreaming"
          class="inline-block w-2 h-4 ml-0.5 bg-current animate-pulse"
        />
      </div>

      <!-- Timestamp -->
      <div
        :class="cn(
          'text-xs mt-1',
          isUser ? 'text-primary-200' : 'text-gray-400'
        )"
      >
        {{ formatRelativeTime(props.message.createdAt) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.typing-indicator span {
  @apply w-2 h-2 bg-gray-400 rounded-full;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
