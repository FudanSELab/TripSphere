import Link from 'next/link'
import Image from 'next/image'
import { MapPin, Star, Clock, DollarSign } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

// Mock data - in production, this would come from API
const attractions = [
  {
    id: '1',
    name: 'The Bund',
    description: 'The Bund is a waterfront area in central Shanghai, featuring a mix of historical colonial-era buildings and modern skyscrapers.',
    city: 'Shanghai',
    country: 'China',
    rating: 4.8,
    category: 'Landmark',
    openingHours: '24 hours',
    ticketPrice: 'Free',
    image: 'https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&h=400&fit=crop',
    tags: ['Historic', 'Scenic', 'Night View', 'Photography'],
  },
  {
    id: '2',
    name: 'Yu Garden',
    description: 'A classical Chinese garden located in the Old City of Shanghai, featuring traditional architecture and landscapes.',
    city: 'Shanghai',
    country: 'China',
    rating: 4.6,
    category: 'Garden',
    openingHours: '8:30 AM - 5:00 PM',
    ticketPrice: '¥40',
    image: 'https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=600&h=400&fit=crop',
    tags: ['Traditional', 'Cultural', 'Architecture'],
  },
  {
    id: '3',
    name: 'Oriental Pearl Tower',
    description: 'An iconic TV tower and landmark of Shanghai with observation decks offering panoramic views of the city.',
    city: 'Shanghai',
    country: 'China',
    rating: 4.5,
    category: 'Landmark',
    openingHours: '9:00 AM - 9:00 PM',
    ticketPrice: '¥160',
    image: 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=600&h=400&fit=crop',
    tags: ['Modern', 'Viewpoint', 'Landmark'],
  },
  {
    id: '4',
    name: 'Forbidden City',
    description: 'The Chinese imperial palace from the Ming dynasty to the end of the Qing dynasty, now a museum.',
    city: 'Beijing',
    country: 'China',
    rating: 4.9,
    category: 'Historical',
    openingHours: '8:30 AM - 5:00 PM',
    ticketPrice: '¥60',
    image: 'https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600&h=400&fit=crop',
    tags: ['Historical', 'Cultural', 'UNESCO'],
  },
  {
    id: '5',
    name: 'West Lake',
    description: 'A UNESCO World Heritage Site featuring beautiful scenery, gardens, and traditional pagodas.',
    city: 'Hangzhou',
    country: 'China',
    rating: 4.7,
    category: 'Nature',
    openingHours: '24 hours',
    ticketPrice: 'Free',
    image: 'https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=600&h=400&fit=crop',
    tags: ['Nature', 'Scenic', 'UNESCO'],
  },
  {
    id: '6',
    name: 'The Humble Administrator\'s Garden',
    description: 'One of the most famous classical gardens in Suzhou, representing traditional Chinese garden design.',
    city: 'Suzhou',
    country: 'China',
    rating: 4.6,
    category: 'Garden',
    openingHours: '7:30 AM - 5:30 PM',
    ticketPrice: '¥70',
    image: 'https://images.unsplash.com/photo-1528164344705-47542687000d?w=600&h=400&fit=crop',
    tags: ['Garden', 'Historical', 'UNESCO'],
  },
]

export default function AttractionsPage() {
  return (
    <div className="bg-gray-50 min-h-screen">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-600 to-secondary-600 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl font-bold mb-4">
              Discover Amazing Attractions
            </h1>
            <p className="text-xl text-white/90 max-w-2xl mx-auto">
              Explore thousands of must-see destinations around the world with personalized recommendations
            </p>
          </div>
        </div>
      </section>

      {/* Attractions Grid */}
      <section className="py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <h2 className="text-2xl font-bold text-gray-900">
              Popular Attractions
            </h2>
            <p className="text-gray-600">
              {attractions.length} attractions found
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {attractions.map((attraction, index) => (
              <Link
                key={attraction.id}
                href={`/attractions/${attraction.id}`}
              >
                <Card hover clickable padding="none" className="h-full overflow-hidden">
                  <div className="relative h-48">
                    <Image
                      src={attraction.image}
                      alt={attraction.name}
                      fill
                      className="object-cover"
                    />
                    <div className="absolute top-4 right-4">
                      <Badge variant="default" className="bg-white text-gray-900 shadow-lg">
                        <Star className="w-3 h-3 fill-yellow-400 text-yellow-400 mr-1" />
                        {attraction.rating}
                      </Badge>
                    </div>
                  </div>

                  <div className="p-5">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="text-xl font-semibold text-gray-900 mb-1">
                          {attraction.name}
                        </h3>
                        <div className="flex items-center gap-1 text-sm text-gray-500">
                          <MapPin className="w-4 h-4" />
                          {attraction.city}, {attraction.country}
                        </div>
                      </div>
                    </div>

                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {attraction.description}
                    </p>

                    <div className="flex flex-wrap gap-2 mb-4">
                      {attraction.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="secondary" size="sm">
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-500 pt-4 border-t border-gray-100">
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {attraction.openingHours}
                      </div>
                      <div className="flex items-center gap-1">
                        <DollarSign className="w-4 h-4" />
                        {attraction.ticketPrice}
                      </div>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
