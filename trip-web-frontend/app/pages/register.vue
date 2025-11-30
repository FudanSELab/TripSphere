<script setup lang="ts">
import { User, Mail, Lock, Eye, EyeOff, Check } from 'lucide-vue-next'

definePageMeta({
  layout: 'default',
})

const auth = useAuth()
const router = useRouter()

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  acceptTerms: false,
})
const showPassword = ref(false)
const showConfirmPassword = ref(false)
const errors = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  acceptTerms: '',
})

const passwordStrength = computed(() => {
  const password = form.password
  if (!password) return { score: 0, label: '', color: '' }
  
  let score = 0
  if (password.length >= 8) score++
  if (/[a-z]/.test(password)) score++
  if (/[A-Z]/.test(password)) score++
  if (/[0-9]/.test(password)) score++
  if (/[^a-zA-Z0-9]/.test(password)) score++

  const levels = [
    { label: 'Weak', color: 'bg-red-500' },
    { label: 'Fair', color: 'bg-orange-500' },
    { label: 'Good', color: 'bg-yellow-500' },
    { label: 'Strong', color: 'bg-green-500' },
    { label: 'Very Strong', color: 'bg-emerald-500' },
  ]

  return { score, ...levels[Math.min(score - 1, 4)] || levels[0] }
})

const validate = () => {
  let isValid = true
  Object.keys(errors).forEach((key) => {
    errors[key as keyof typeof errors] = ''
  })

  if (!form.username) {
    errors.username = 'Username is required'
    isValid = false
  } else if (form.username.length < 3) {
    errors.username = 'Username must be at least 3 characters'
    isValid = false
  }

  if (!form.email) {
    errors.email = 'Email is required'
    isValid = false
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Please enter a valid email address'
    isValid = false
  }

  if (!form.password) {
    errors.password = 'Password is required'
    isValid = false
  } else if (form.password.length < 8) {
    errors.password = 'Password must be at least 8 characters'
    isValid = false
  }

  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match'
    isValid = false
  }

  if (!form.acceptTerms) {
    errors.acceptTerms = 'You must accept the terms and conditions'
    isValid = false
  }

  return isValid
}

const handleSubmit = async () => {
  if (!validate()) return

  const success = await auth.register({
    username: form.username,
    email: form.email,
    password: form.password,
  })

  if (success) {
    router.push('/')
  }
}
</script>

<template>
  <div class="min-h-[calc(100vh-64px)] flex items-center justify-center bg-gray-50 py-12 px-4">
    <div class="w-full max-w-md">
      <!-- Card -->
      <UiCard class="animate-fade-in-up">
        <!-- Header -->
        <div class="text-center mb-8">
          <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center mx-auto mb-4 text-white text-2xl font-bold">
            T
          </div>
          <h1 class="text-2xl font-bold text-gray-900">Create an account</h1>
          <p class="text-gray-500 mt-2">Start your journey with TripSphere</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit">
          <div class="space-y-5">
            <!-- Username -->
            <UiInput
              v-model="form.username"
              label="Username"
              placeholder="Choose a username"
              :error="errors.username"
            >
              <template #prepend>
                <User class="w-5 h-5" />
              </template>
            </UiInput>

            <!-- Email -->
            <UiInput
              v-model="form.email"
              type="email"
              label="Email address"
              placeholder="Enter your email"
              :error="errors.email"
            >
              <template #prepend>
                <Mail class="w-5 h-5" />
              </template>
            </UiInput>

            <!-- Password -->
            <div>
              <UiInput
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                label="Password"
                placeholder="Create a password"
                :error="errors.password"
              >
                <template #prepend>
                  <Lock class="w-5 h-5" />
                </template>
                <template #append>
                  <button
                    type="button"
                    class="text-gray-400 hover:text-gray-600"
                    @click="showPassword = !showPassword"
                  >
                    <Eye v-if="!showPassword" class="w-5 h-5" />
                    <EyeOff v-else class="w-5 h-5" />
                  </button>
                </template>
              </UiInput>

              <!-- Password strength -->
              <div v-if="form.password" class="mt-2">
                <div class="flex gap-1 mb-1">
                  <div
                    v-for="i in 5"
                    :key="i"
                    :class="[
                      'h-1 flex-1 rounded-full transition-colors',
                      i <= passwordStrength.score ? passwordStrength.color : 'bg-gray-200'
                    ]"
                  />
                </div>
                <p class="text-xs text-gray-500">
                  Password strength: <span :class="passwordStrength.score >= 3 ? 'text-green-600' : 'text-orange-600'">{{ passwordStrength.label }}</span>
                </p>
              </div>
            </div>

            <!-- Confirm Password -->
            <UiInput
              v-model="form.confirmPassword"
              :type="showConfirmPassword ? 'text' : 'password'"
              label="Confirm password"
              placeholder="Confirm your password"
              :error="errors.confirmPassword"
            >
              <template #prepend>
                <Lock class="w-5 h-5" />
              </template>
              <template #append>
                <button
                  type="button"
                  class="text-gray-400 hover:text-gray-600"
                  @click="showConfirmPassword = !showConfirmPassword"
                >
                  <Eye v-if="!showConfirmPassword" class="w-5 h-5" />
                  <EyeOff v-else class="w-5 h-5" />
                </button>
              </template>
            </UiInput>

            <!-- Terms and conditions -->
            <div>
              <label class="flex items-start gap-3 cursor-pointer">
                <input
                  v-model="form.acceptTerms"
                  type="checkbox"
                  class="mt-1 w-4 h-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span class="text-sm text-gray-600">
                  I agree to the 
                  <a href="#" class="text-primary-600 hover:text-primary-700 font-medium">Terms of Service</a>
                  and
                  <a href="#" class="text-primary-600 hover:text-primary-700 font-medium">Privacy Policy</a>
                </span>
              </label>
              <p
                v-if="errors.acceptTerms"
                class="mt-1 text-sm text-red-500"
              >
                {{ errors.acceptTerms }}
              </p>
            </div>

            <!-- Error message -->
            <p
              v-if="auth.error.value"
              class="text-sm text-red-500 text-center"
            >
              {{ auth.error.value }}
            </p>

            <!-- Submit button -->
            <UiButton
              type="submit"
              class="w-full"
              size="lg"
              :loading="auth.isLoading.value"
            >
              Create Account
            </UiButton>
          </div>
        </form>

        <!-- Sign in link -->
        <p class="text-center text-sm text-gray-500 mt-8">
          Already have an account?
          <NuxtLink to="/login" class="text-primary-600 hover:text-primary-700 font-medium">
            Sign in
          </NuxtLink>
        </p>
      </UiCard>
    </div>
  </div>
</template>
