<script setup lang="ts">
import { cn } from '~/utils'

interface Props {
  variant?: 'default' | 'secondary' | 'outline' | 'success' | 'warning' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  removable?: boolean
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'md',
  removable: false,
})

const emit = defineEmits<{
  remove: []
}>()

const variantClasses = {
  default: 'bg-primary-100 text-primary-700',
  secondary: 'bg-gray-100 text-gray-700',
  outline: 'bg-transparent border border-gray-300 text-gray-700',
  success: 'bg-green-100 text-green-700',
  warning: 'bg-amber-100 text-amber-700',
  danger: 'bg-red-100 text-red-700',
}

const sizeClasses = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-2.5 py-1 text-sm',
  lg: 'px-3 py-1.5 text-base',
}
</script>

<template>
  <span
    :class="cn(
      'inline-flex items-center gap-1 rounded-full font-medium',
      variantClasses[props.variant],
      sizeClasses[props.size],
      props.class
    )"
  >
    <slot />
    <button
      v-if="props.removable"
      type="button"
      class="ml-1 rounded-full p-0.5 hover:bg-black/10 transition-colors"
      @click="emit('remove')"
    >
      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  </span>
</template>
