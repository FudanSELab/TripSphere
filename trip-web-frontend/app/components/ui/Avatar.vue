<script setup lang="ts">
import { getAvatarColor, getInitials, cn } from '~/utils'

interface Props {
  src?: string
  alt?: string
  name?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
})

const sizeClasses = {
  xs: 'w-6 h-6 text-xs',
  sm: 'w-8 h-8 text-sm',
  md: 'w-10 h-10 text-base',
  lg: 'w-12 h-12 text-lg',
  xl: 'w-16 h-16 text-xl',
}

const initials = computed(() => props.name ? getInitials(props.name) : '?')
const bgColor = computed(() => props.name ? getAvatarColor(props.name) : 'bg-gray-400')
const imageError = ref(false)

const showFallback = computed(() => !props.src || imageError.value)
</script>

<template>
  <div
    :class="cn(
      'relative rounded-full overflow-hidden flex items-center justify-center font-semibold text-white',
      sizeClasses[props.size],
      showFallback && bgColor,
      props.class
    )"
  >
    <img
      v-if="props.src && !imageError"
      :src="props.src"
      :alt="props.alt || props.name || 'Avatar'"
      class="w-full h-full object-cover"
      @error="imageError = true"
    />
    <span v-else>{{ initials }}</span>
  </div>
</template>
