<script setup lang="ts">
import { cn } from '~/utils'

interface Props {
  class?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hover?: boolean
  clickable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  padding: 'md',
  hover: false,
  clickable: false,
})

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-7',
}
</script>

<template>
  <div
    :class="cn(
      'bg-white rounded-xl border border-gray-100 shadow-sm',
      paddingClasses[props.padding],
      props.hover && 'card-hover',
      props.clickable && 'cursor-pointer',
      props.class
    )"
  >
    <slot />
  </div>
</template>
