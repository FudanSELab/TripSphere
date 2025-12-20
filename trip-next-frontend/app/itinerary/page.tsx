'use client'

import { useState, useMemo } from 'react'
import { 
  Calendar,
  MapPin,
  Clock,
  Plus,
  ChevronRight,
  ChevronDown,
  Sparkles,
  Loader2,
  GripVertical,
  Trash2,
  Edit3,
  Save
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { Itinerary, DayPlan, Activity } from '@/lib/types'

const availableInterests = [
  'Culture', 'Food', 'Nature', 'Adventure', 'Shopping', 
  'History', 'Art', 'Nightlife', 'Family', 'Photography'
]

const budgetOptions = [
  { value: 'budget', label: 'Budget', description: 'Economical options' },
  { value: 'moderate', label: 'Moderate', description: 'Balanced comfort' },
  { value: 'luxury', label: 'Luxury', description: 'Premium experience' },
]

export default function ItineraryPage() {
  // Form state
  const [destination, setDestination] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [interests, setInterests] = useState<string[]>([])
  const [budgetLevel, setBudgetLevel] = useState<'budget' | 'moderate' | 'luxury'>('moderate')
  const [numTravelers, setNumTravelers] = useState(2)

  // Generated itinerary state
  const [itinerary, setItinerary] = useState<Itinerary | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [generationStatus, setGenerationStatus] = useState('')
  const [expandedDays, setExpandedDays] = useState<number[]>([1])

  // Toggle interest selection
  const toggleInterest = (interest: string) => {
    setInterests(prev => 
      prev.includes(interest) 
        ? prev.filter(i => i !== interest)
        : [...prev, interest]
    )
  }

  // Generate itinerary
  const generateItinerary = async () => {
    if (!destination || !startDate || !endDate) {
      return
    }

    setIsGenerating(true)
    setGenerationProgress(0)
    setGenerationStatus('Analyzing your preferences...')

    // Simulate AI generation with progress
    const steps = [
      { progress: 20, status: 'Researching destination...' },
      { progress: 40, status: 'Finding best attractions...' },
      { progress: 60, status: 'Optimizing route...' },
      { progress: 80, status: 'Adding recommendations...' },
      { progress: 100, status: 'Finalizing itinerary...' },
    ]

    for (const step of steps) {
      await new Promise(resolve => setTimeout(resolve, 800))
      setGenerationProgress(step.progress)
      setGenerationStatus(step.status)
    }

    // Mock generated itinerary
    const start = new Date(startDate)
    const end = new Date(endDate)
    const numDays = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1

    const mockDayPlans: DayPlan[] = Array.from({ length: numDays }, (_, i) => {
      const date = new Date(start)
      date.setDate(date.getDate() + i)
      
      return {
        dayNumber: i + 1,
        date: date.toISOString().split('T')[0],
        activities: [
          {
            id: `${i}-1`,
            name: i === 0 ? 'Arrival & Check-in' : `Morning at ${['West Lake', 'The Bund', 'Yu Garden', 'Temple'][i % 4]}`,
            description: 'Start your day with a visit to this iconic location.',
            startTime: '09:00',
            endTime: '12:00',
            location: { name: destination, latitude: 31.23, longitude: 121.47, address: destination },
            category: 'sightseeing',
            cost: { amount: 0, currency: 'CNY' },
          },
          {
            id: `${i}-2`,
            name: `Lunch at Local Restaurant`,
            description: 'Enjoy authentic local cuisine at a recommended restaurant.',
            startTime: '12:30',
            endTime: '14:00',
            location: { name: 'Local Restaurant', latitude: 31.23, longitude: 121.47, address: destination },
            category: 'dining',
            cost: { amount: 150, currency: 'CNY' },
          },
          {
            id: `${i}-3`,
            name: i === numDays - 1 ? 'Departure' : `Afternoon at ${['Shopping District', 'Museum', 'Park', 'Landmark'][i % 4]}`,
            description: 'Continue exploring the city and its attractions.',
            startTime: '15:00',
            endTime: '18:00',
            location: { name: destination, latitude: 31.23, longitude: 121.47, address: destination },
            category: i === numDays - 1 ? 'transportation' : 'sightseeing',
            cost: { amount: 80, currency: 'CNY' },
          },
        ],
        notes: i === 0 ? 'Remember to exchange currency and get a local SIM card.' : '',
      }
    })

    setItinerary({
      id: 'itinerary-' + Date.now(),
      destination: destination,
      startDate: startDate,
      endDate: endDate,
      dayPlans: mockDayPlans,
      summary: {
        totalEstimatedCost: numDays * 230,
        currency: 'CNY',
        totalActivities: numDays * 3,
        highlights: ['Local cuisine experience', 'Cultural immersion', 'Scenic landmarks'],
      },
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    })

    setExpandedDays([1])
    setIsGenerating(false)
  }

  // Toggle day expansion
  const toggleDay = (dayNumber: number) => {
    setExpandedDays(prev =>
      prev.includes(dayNumber)
        ? prev.filter(d => d !== dayNumber)
        : [...prev, dayNumber]
    )
  }

  // Format date for display
  const formatDayDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
  }

  // Get activity category color
  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      sightseeing: 'bg-blue-100 text-blue-700',
      dining: 'bg-orange-100 text-orange-700',
      transportation: 'bg-gray-100 text-gray-700',
      shopping: 'bg-pink-100 text-pink-700',
      entertainment: 'bg-purple-100 text-purple-700',
    }
    return colors[category] || 'bg-gray-100 text-gray-700'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero section */}
      <div className="bg-gradient-to-br from-green-600 to-emerald-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <span className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 rounded-full text-sm font-medium mb-4">
              <Sparkles className="w-4 h-4" />
              AI-Powered Planning
            </span>
            <h1 className="text-4xl sm:text-5xl font-bold mb-4">Plan Your Perfect Trip</h1>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              Let our AI create a personalized itinerary based on your preferences, interests, and travel style.
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Planning form */}
          <div className="lg:col-span-1">
            <Card className="sticky top-24">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Trip Details</h2>
              
              <form className="space-y-5" onSubmit={(e) => { e.preventDefault(); generateItinerary(); }}>
                {/* Destination */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Destination
                  </label>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      value={destination}
                      onChange={(e) => setDestination(e.target.value)}
                      placeholder="e.g., Shanghai, China"
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                    />
                  </div>
                </div>

                {/* Travelers */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Travelers
                  </label>
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      className="w-10 h-10 rounded-lg border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-50 disabled:opacity-50"
                      disabled={numTravelers <= 1}
                      onClick={() => setNumTravelers(Math.max(1, numTravelers - 1))}
                    >
                      -
                    </button>
                    <span className="text-lg font-medium text-gray-900 w-8 text-center">
                      {numTravelers}
                    </span>
                    <button
                      type="button"
                      className="w-10 h-10 rounded-lg border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-50"
                      onClick={() => setNumTravelers(numTravelers + 1)}
                    >
                      +
                    </button>
                  </div>
                </div>

                {/* Budget level */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Budget Level
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {budgetOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        className={`p-3 rounded-lg border text-center transition-all ${
                          budgetLevel === option.value
                            ? 'border-green-500 bg-green-50 text-green-700'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => setBudgetLevel(option.value as 'budget' | 'moderate' | 'luxury')}
                      >
                        <div className="text-sm font-medium">{option.label}</div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Interests */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Interests
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {availableInterests.map((interest) => (
                      <button
                        key={interest}
                        type="button"
                        className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                          interests.includes(interest)
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                        onClick={() => toggleInterest(interest)}
                      >
                        {interest}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Generate button */}
                <Button
                  type="submit"
                  className="w-full"
                  size="lg"
                  disabled={!destination || !startDate || !endDate || isGenerating}
                >
                  {isGenerating ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Generate Itinerary
                    </>
                  )}
                </Button>
              </form>
            </Card>
          </div>

          {/* Itinerary display */}
          <div className="lg:col-span-2">
            {/* Loading state */}
            {isGenerating && (
              <div className="text-center py-16">
                <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
                  <Loader2 className="w-10 h-10 text-green-600 animate-spin" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {generationStatus}
                </h3>
                <div className="w-64 h-2 bg-gray-200 rounded-full mx-auto overflow-hidden">
                  <div
                    className="h-full bg-green-600 rounded-full transition-all duration-500"
                    style={{ width: `${generationProgress}%` }}
                  />
                </div>
                <p className="text-gray-500 mt-4">
                  This may take a moment...
                </p>
              </div>
            )}

            {/* Empty state */}
            {!isGenerating && !itinerary && (
              <div className="text-center py-16">
                <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
                  <Calendar className="w-10 h-10 text-green-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Ready to plan your trip?
                </h3>
                <p className="text-gray-500 max-w-md mx-auto">
                  Fill in your trip details on the left and let our AI create a personalized itinerary just for you.
                </p>
              </div>
            )}

            {/* Generated itinerary */}
            {!isGenerating && itinerary && (
              <div className="space-y-6">
                {/* Summary card */}
                <Card>
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">
                        {itinerary.destination}
                      </h2>
                      <p className="text-gray-500 mt-1">
                        {formatDayDate(itinerary.startDate)} - {formatDayDate(itinerary.endDate)}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm">
                        <Edit3 className="w-4 h-4" />
                        Edit
                      </Button>
                      <Button variant="default" size="sm">
                        <Save className="w-4 h-4" />
                        Save
                      </Button>
                    </div>
                  </div>

                  {/* Summary stats */}
                  <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-gray-100">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {itinerary.dayPlans.length}
                      </div>
                      <div className="text-sm text-gray-500">Days</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {itinerary.summary?.totalActivities}
                      </div>
                      <div className="text-sm text-gray-500">Activities</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        ¥{itinerary.summary?.totalEstimatedCost}
                      </div>
                      <div className="text-sm text-gray-500">Est. Cost</div>
                    </div>
                  </div>

                  {/* Highlights */}
                  {itinerary.summary?.highlights && itinerary.summary.highlights.length > 0 && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Highlights</h4>
                      <div className="flex flex-wrap gap-2">
                        {itinerary.summary.highlights.map((highlight) => (
                          <Badge
                            key={highlight}
                            className="bg-green-100 text-green-700"
                          >
                            {highlight}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>

                {/* Day by day itinerary */}
                <div className="space-y-4">
                  {itinerary.dayPlans.map((day) => (
                    <Card key={day.dayNumber} padding="none">
                      {/* Day header */}
                      <button
                        className="w-full flex items-center justify-between p-5 hover:bg-gray-50 transition-colors"
                        onClick={() => toggleDay(day.dayNumber)}
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center text-green-600 font-bold">
                            {day.dayNumber}
                          </div>
                          <div className="text-left">
                            <h3 className="font-semibold text-gray-900">Day {day.dayNumber}</h3>
                            <p className="text-sm text-gray-500">{formatDayDate(day.date)}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-gray-500">
                            {day.activities.length} activities
                          </span>
                          <ChevronDown
                            className={`w-5 h-5 text-gray-400 transition-transform ${
                              expandedDays.includes(day.dayNumber) ? 'rotate-180' : ''
                            }`}
                          />
                        </div>
                      </button>

                      {/* Day activities */}
                      {expandedDays.includes(day.dayNumber) && (
                        <div className="border-t border-gray-100">
                          <div className="p-5 space-y-4">
                            {day.activities.map((activity) => (
                              <div
                                key={activity.id}
                                className="flex gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group"
                              >
                                {/* Time */}
                                <div className="flex-shrink-0 text-center">
                                  <div className="text-sm font-medium text-gray-900">
                                    {activity.startTime}
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    {activity.endTime}
                                  </div>
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-start justify-between gap-2">
                                    <div>
                                      <h4 className="font-medium text-gray-900">
                                        {activity.name}
                                      </h4>
                                      <p className="text-sm text-gray-500 mt-1">
                                        {activity.description}
                                      </p>
                                    </div>
                                    <Badge
                                      className={getCategoryColor(activity.category)}
                                      size="sm"
                                    >
                                      {activity.category}
                                    </Badge>
                                  </div>

                                  <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                                    <span className="flex items-center gap-1">
                                      <MapPin className="w-4 h-4" />
                                      {activity.location.name}
                                    </span>
                                    {activity.cost?.amount ? (
                                      <span className="flex items-center gap-1">
                                        ¥{activity.cost.amount}
                                      </span>
                                    ) : null}
                                  </div>
                                </div>

                                {/* Actions */}
                                <div className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                                  <button className="p-2 hover:bg-white rounded-lg text-gray-400 hover:text-gray-600">
                                    <GripVertical className="w-4 h-4" />
                                  </button>
                                </div>
                              </div>
                            ))}

                            {/* Add activity button */}
                            <button className="w-full py-3 border-2 border-dashed border-gray-200 rounded-xl text-gray-400 hover:border-green-500 hover:text-green-600 transition-colors flex items-center justify-center gap-2">
                              <Plus className="w-4 h-4" />
                              Add Activity
                            </button>

                            {/* Day notes */}
                            {day.notes && (
                              <div className="p-4 bg-amber-50 rounded-xl border border-amber-100">
                                <p className="text-sm text-amber-800">
                                  <strong>Note:</strong> {day.notes}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
