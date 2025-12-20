'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Lock, User, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { useAuth } from '@/lib/hooks/use-auth'

export default function RegisterPage() {
  const router = useRouter()
  const auth = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [usernameError, setUsernameError] = useState('')
  const [passwordError, setPasswordError] = useState('')

  // Username validation: allows letters, numbers, and underscores
  const validateUsername = (value: string): string => {
    if (!value || value.trim() === '') {
      return 'Please input username.'
    }
    if (!/^[a-zA-Z0-9_]+$/.test(value)) {
      return 'Usernames can only contain letters, numbers, and underscores.'
    }
    return ''
  }

  // Password validation: at least 6 characters, only letters and numbers
  const validatePassword = (value: string): string => {
    if (value.length < 6) {
      return 'Password must be at least 6 characters long.'
    }
    if (!/^[a-zA-Z0-9]+$/.test(value)) {
      return 'Password can only contain letters and numbers.'
    }
    return ''
  }

  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setUsername(value)
    setUsernameError(validateUsername(value))
  }

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setPassword(value)
    setPasswordError(validatePassword(value))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setUsernameError('')
    setPasswordError('')

    // Validate username
    const usernameErr = validateUsername(username)
    if (usernameErr) {
      setUsernameError(usernameErr)
      return
    }

    // Validate password
    const passwordErr = validatePassword(password)
    if (passwordErr) {
      setPasswordError(passwordErr)
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    const success = await auth.register({ username, password })
    if (success) {
      router.push('/login')
    } else {
      setError(auth.error || 'Registration failed. Please try again.')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-secondary-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md" padding="lg">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-2xl">
            T
          </div>
          <h2 className="text-3xl font-bold text-gray-900">Create Account</h2>
          <p className="mt-2 text-gray-600">
            Join TripSphere and start planning your perfect trip
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <Input
            label="Username"
            type="text"
            value={username}
            onChange={handleUsernameChange}
            placeholder="Choose a username"
            prepend={<User className="w-5 h-5" />}
            error={usernameError}
            required
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={handlePasswordChange}
            placeholder="Create a password"
            prepend={<Lock className="w-5 h-5" />}
            error={passwordError}
            hint={!passwordError ? "Must be at least 6 characters" : undefined}
            required
          />

          <Input
            label="Confirm Password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Confirm your password"
            prepend={<Lock className="w-5 h-5" />}
            required
          />

          <div className="flex items-start">
            <input
              type="checkbox"
              className="w-4 h-4 mt-1 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
              required
            />
            <label className="ml-2 text-sm text-gray-600">
              I agree to the{' '}
              <Link href="/terms" className="text-primary-600 hover:text-primary-700">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link href="/privacy" className="text-primary-600 hover:text-primary-700">
                Privacy Policy
              </Link>
            </label>
          </div>

          <Button
            type="submit"
            className="w-full"
            size="lg"
            loading={auth.isLoading}
          >
            Create Account
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <Link
              href="/login"
              className="font-medium text-primary-600 hover:text-primary-700"
            >
              Sign in
            </Link>
          </p>
        </div>
      </Card>
    </div>
  )
}
