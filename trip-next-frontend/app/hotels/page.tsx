'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Hotel, MapPin, Star, Search, Filter, ChevronDown, Heart, Wifi, Car, Coffee, Dumbbell } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { Hotel as HotelType } from '@/lib/types'

// Mock data for hotels
const mockHotels: HotelType[] = [
  {
    id: '1',
    name: 'The Peninsula Shanghai',
    address: { country: 'China', province: 'Shanghai', city: 'Shanghai', county: 'Huangpu', district: '', street: 'No. 32 Zhongshan East 1st Road' },
    introduction: 'A luxurious 5-star hotel overlooking the historic Bund and the modern Pudong skyline.',
    tags: ['Luxury', '5-Star', 'River View', 'Spa', 'Restaurant'],
    rooms: [
      { name: 'Deluxe Room', totalNumber: 50, remainingNumber: 10, bedWidth: 2.0, bedNumber: 1, minArea: 55, maxArea: 60, peopleNumber: 2, tags: ['City View'] },
      { name: 'Premier Suite', totalNumber: 20, remainingNumber: 5, bedWidth: 2.0, bedNumber: 1, minArea: 88, maxArea: 95, peopleNumber: 2, tags: ['River View', 'Living Room'] },
    ],
    location: { lng: 121.4883, lat: 31.2365 },
    rating: 4.9,
    priceRange: '¥3,500 - ¥15,000',
    images: ['https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop'],
  },
  {
    id: '2',
    name: 'Hyatt on the Bund',
    address: { country: 'China', province: 'Shanghai', city: 'Shanghai', county: 'Hongkou', district: '', street: 'No. 199 Huangpu Road' },
    introduction: 'Modern luxury hotel with stunning views of the Huangpu River and city skyline.',
    tags: ['Business', '5-Star', 'River View', 'Pool', 'Gym'],
    rooms: [
      { name: 'Grand Room', totalNumber: 80, remainingNumber: 25, bedWidth: 1.8, bedNumber: 1, minArea: 40, maxArea: 45, peopleNumber: 2, tags: ['City View'] },
      { name: 'River View Suite', totalNumber: 30, remainingNumber: 8, bedWidth: 2.0, bedNumber: 1, minArea: 65, maxArea: 75, peopleNumber: 2, tags: ['River View'] },
    ],
    location: { lng: 121.4928, lat: 31.2456 },
    rating: 4.7,
    priceRange: '¥1,800 - ¥6,500',
    images: ['https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&h=400&fit=crop'],
  },
  {
    id: '3',
    name: 'Mandarin Oriental Pudong',
    address: { country: 'China', province: 'Shanghai', city: 'Shanghai', county: 'Pudong', district: '', street: 'No. 111 Pudong South Road' },
    introduction: 'Elegant hotel in the heart of Lujiazui financial district with world-class amenities.',
    tags: ['Luxury', '5-Star', 'Spa', 'Fine Dining', 'Business Center'],
    rooms: [
      { name: 'Superior Room', totalNumber: 100, remainingNumber: 30, bedWidth: 1.8, bedNumber: 1, minArea: 45, maxArea: 50, peopleNumber: 2, tags: ['City View'] },
      { name: 'Club Suite', totalNumber: 25, remainingNumber: 7, bedWidth: 2.0, bedNumber: 1, minArea: 80, maxArea: 90, peopleNumber: 2, tags: ['Club Access', 'River View'] },
    ],
    location: { lng: 121.5032, lat: 31.2308 },
    rating: 4.8,
    priceRange: '¥2,500 - ¥12,000',
    images: ['https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600&h=400&fit=crop'],
  },
  {
    id: '4',
    name: 'Four Seasons Hangzhou',
    address: { country: 'China', province: 'Zhejiang', city: 'Hangzhou', county: '', district: '', street: 'No. 5 Lingyin Road' },
    introduction: 'A tranquil retreat nestled beside West Lake with traditional Chinese architecture.',
    tags: ['Resort', '5-Star', 'Lake View', 'Spa', 'Garden'],
    rooms: [
      { name: 'Garden View Room', totalNumber: 60, remainingNumber: 15, bedWidth: 1.8, bedNumber: 1, minArea: 50, maxArea: 55, peopleNumber: 2, tags: ['Garden View'] },
      { name: 'West Lake Suite', totalNumber: 15, remainingNumber: 3, bedWidth: 2.0, bedNumber: 1, minArea: 100, maxArea: 120, peopleNumber: 2, tags: ['Lake View', 'Balcony'] },
    ],
    location: { lng: 120.1285, lat: 30.2521 },
    rating: 4.9,
    priceRange: '¥3,200 - ¥18,000',
    images: ['https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&h=400&fit=crop'],
  },
  {
    id: '5',
    name: 'Waldorf Astoria Beijing',
    address: { country: 'China', province: 'Beijing', city: 'Beijing', county: 'Dongcheng', district: '', street: 'No. 5-15 Jinyu Hutong' },
    introduction: 'Historic Art Deco hotel offering exceptional service in the heart of Beijing.',
    tags: ['Historic', '5-Star', 'Central Location', 'Restaurant', 'Bar'],
    rooms: [
      { name: 'Deluxe King', totalNumber: 70, remainingNumber: 20, bedWidth: 2.0, bedNumber: 1, minArea: 52, maxArea: 58, peopleNumber: 2, tags: ['City View'] },
      { name: 'Hutong Suite', totalNumber: 12, remainingNumber: 2, bedWidth: 2.0, bedNumber: 1, minArea: 110, maxArea: 130, peopleNumber: 2, tags: ['Hutong View', 'Living Room'] },
    ],
    location: { lng: 116.4142, lat: 39.9149 },
    rating: 4.8,
    priceRange: '¥2,800 - ¥20,000',
    images: ['https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600&h=400&fit=crop'],
  },
]

const categories = ['All', 'Luxury', 'Business', 'Resort', 'Historic']

export default function HotelsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)

  const filteredHotels = useMemo(() => {
    let result = mockHotels

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(
        h => h.name.toLowerCase().includes(query) ||
             h.introduction.toLowerCase().includes(query) ||
             h.address.city.toLowerCase().includes(query) ||
             h.tags?.some(t => t.toLowerCase().includes(query))
      )
    }

    if (selectedCategory && selectedCategory !== 'All') {
      result = result.filter(h => h.tags?.includes(selectedCategory))
    }

    return result
  }, [searchQuery, selectedCategory])

  const selectCategory = (category: string) => {
    setSelectedCategory(category === 'All' ? null : category)
  }

  const getLowestPrice = (hotel: HotelType) => {
    return hotel.priceRange?.split(' - ')[0] || 'N/A'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero section */}
      <div className="bg-gradient-to-br from-secondary-600 to-accent-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl font-bold mb-4">Find Your Perfect Stay</h1>
            <p className="text-xl text-white/80 max-w-2xl mx-auto mb-8">
              Discover handpicked hotels with AI-powered recommendations for your ideal trip.
            </p>
            
            {/* Search bar */}
            <div className="max-w-2xl mx-auto">
              <div className="relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  type="text"
                  placeholder="Search hotels, cities, or amenities..."
                  className="w-full pl-12 pr-4 py-4 rounded-xl text-gray-900 bg-white shadow-lg focus:outline-none focus:ring-4 focus:ring-white/30 transition-all"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="flex items-center justify-between mb-8">
          {/* Categories */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {categories.map((category) => (
              <button
                key={category}
                className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  (category === 'All' && !selectedCategory) || selectedCategory === category
                    ? 'bg-secondary-600 text-white shadow-md'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                }`}
                onClick={() => selectCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>

          {/* Filter button */}
          <button
            className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg text-gray-700 border border-gray-200 hover:bg-gray-50 transition-colors"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-4 h-4" />
            Filters
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Results count */}
        <p className="text-gray-600 mb-6">
          {filteredHotels.length} hotels found
        </p>

        {/* Hotels grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredHotels.map((hotel) => (
            <Link
              key={hotel.id}
              href={`/hotels/${hotel.id}`}
              className="group"
            >
              <Card padding="none" hover clickable>
                {/* Image */}
                <div className="relative aspect-[4/3] overflow-hidden rounded-t-xl">
                  <img
                    src={hotel.images?.[0]}
                    alt={hotel.name}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  {/* Overlay badges */}
                  <div className="absolute top-3 left-3 flex gap-2">
                    <Badge variant="secondary" size="sm">
                      {hotel.tags?.[0]}
                    </Badge>
                  </div>
                  {/* Like button */}
                  <button
                    className="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/90 flex items-center justify-center text-gray-600 hover:text-red-500 hover:bg-white transition-all"
                    onClick={(e) => e.preventDefault()}
                  >
                    <Heart className="w-5 h-5" />
                  </button>
                  {/* Price badge */}
                  <div className="absolute bottom-3 right-3 px-3 py-1.5 bg-white/95 rounded-lg shadow-lg">
                    <span className="text-sm font-bold text-secondary-600">From {getLowestPrice(hotel)}</span>
                    <span className="text-xs text-gray-500">/night</span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-5">
                  {/* Title and rating */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="text-lg font-semibold text-gray-900 group-hover:text-secondary-600 transition-colors">
                      {hotel.name}
                    </h3>
                    <div className="flex items-center gap-1 text-amber-500">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm font-medium text-gray-700">{hotel.rating}</span>
                    </div>
                  </div>

                  {/* Location */}
                  <p className="flex items-center gap-1 text-sm text-gray-500 mb-3">
                    <MapPin className="w-4 h-4" />
                    {hotel.address.city}, {hotel.address.country}
                  </p>

                  {/* Description */}
                  <p className="text-gray-600 text-sm line-clamp-2 mb-4">
                    {hotel.introduction}
                  </p>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {hotel.tags?.slice(1, 4).map((tag) => (
                      <Badge
                        key={tag}
                        variant="outline"
                        size="sm"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>

                  {/* Room info */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                    <div className="text-sm text-gray-500">
                      {hotel.rooms?.length || 0} room types available
                    </div>
                    <Button variant="ghost" size="sm">
                      View Details
                    </Button>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>

        {/* Empty state */}
        {filteredHotels.length === 0 && (
          <div className="text-center py-16">
            <Hotel className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No hotels found</h3>
            <p className="text-gray-500">Try adjusting your search or filters</p>
          </div>
        )}
      </div>
    </div>
  )
}
