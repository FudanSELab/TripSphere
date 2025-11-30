<script setup lang="ts">
import { cn } from '~/utils'

interface Props {
  modelValue: string
  type?: 'text' | 'email' | 'password' | 'search' | 'tel' | 'url' | 'number'
  placeholder?: string
  disabled?: boolean
  readonly?: boolean
  error?: string
  label?: string
  hint?: string
  icon?: string
  class?: string
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  placeholder: '',
  disabled: false,
  readonly: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  keydown: [event: KeyboardEvent]
}>()

const inputRef = ref<HTMLInputElement | null>(null)
const isFocused = ref(false)

const inputValue = computed({
  get: () => props.modelValue,
  set: (value: string) => emit('update:modelValue', value),
})

const handleFocus = (event: FocusEvent) => {
  isFocused.value = true
  emit('focus', event)
}

const handleBlur = (event: FocusEvent) => {
  isFocused.value = false
  emit('blur', event)
}

const focus = () => {
  inputRef.value?.focus()
}

defineExpose({ focus, inputRef })
</script>

<template>
  <div class="w-full">
    <label
      v-if="props.label"
      class="block text-sm font-medium text-gray-700 mb-1.5"
    >
      {{ props.label }}
    </label>
    <div class="relative">
      <div
        v-if="$slots.prepend"
        class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-400"
      >
        <slot name="prepend" />
      </div>
      <input
        ref="inputRef"
        v-model="inputValue"
        :type="props.type"
        :placeholder="props.placeholder"
        :disabled="props.disabled"
        :readonly="props.readonly"
        :class="cn(
          'w-full px-4 py-2.5 text-gray-900 bg-white border rounded-lg transition-all duration-200',
          'placeholder:text-gray-400',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent',
          'disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed',
          props.error 
            ? 'border-red-500 focus:ring-red-500' 
            : 'border-gray-200 hover:border-gray-300',
          $slots.prepend ? 'pl-10' : '',
          $slots.append ? 'pr-10' : '',
          props.class
        )"
        @focus="handleFocus"
        @blur="handleBlur"
        @keydown="emit('keydown', $event)"
      />
      <div
        v-if="$slots.append"
        class="absolute inset-y-0 right-0 flex items-center pr-3"
      >
        <slot name="append" />
      </div>
    </div>
    <p
      v-if="props.error"
      class="mt-1.5 text-sm text-red-500"
    >
      {{ props.error }}
    </p>
    <p
      v-else-if="props.hint"
      class="mt-1.5 text-sm text-gray-500"
    >
      {{ props.hint }}
    </p>
  </div>
</template>
