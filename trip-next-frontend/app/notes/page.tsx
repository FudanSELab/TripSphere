'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { 
  FileText, 
  Plus, 
  Search, 
  Heart, 
  Clock,
  Edit3,
  Trash2
} from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/lib/hooks/use-auth'
import { formatRelativeTime } from '@/lib/utils'
import type { Note } from '@/lib/types'

// Mock notes data
const mockNotes: Note[] = [
  {
    id: '1',
    userId: 'user1',
    title: 'Amazing Weekend in Shanghai',
    content: 'My trip to Shanghai was absolutely incredible! From the historic Bund to the modern Pudong skyline, every moment was memorable. The food was exceptional, especially the xiaolongbao at Din Tai Fung...',
    coverImage: 'https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&h=400&fit=crop',
    tags: ['Shanghai', 'City Trip', 'Food'],
    likes: 245,
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-01-15T10:00:00Z',
    published: true,
  },
  {
    id: '2',
    userId: 'user2',
    title: 'West Lake: A Photographer\'s Paradise',
    content: 'As a photographer, West Lake in Hangzhou has always been on my bucket list. The misty mornings, traditional pagodas, and serene waters create the perfect backdrop for stunning photos...',
    coverImage: 'https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=600&h=400&fit=crop',
    tags: ['Hangzhou', 'Photography', 'Nature'],
    likes: 189,
    createdAt: '2024-01-14T15:30:00Z',
    updatedAt: '2024-01-14T15:30:00Z',
    published: true,
  },
  {
    id: '3',
    userId: 'user3',
    title: 'Hidden Gems of Beijing Hutongs',
    content: 'Wandering through Beijing\'s ancient hutongs was like stepping back in time. The narrow alleyways are filled with history, local eateries, and charming courtyard homes that tell stories of old Beijing...',
    coverImage: 'https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600&h=400&fit=crop',
    tags: ['Beijing', 'Culture', 'History'],
    likes: 312,
    createdAt: '2024-01-13T09:15:00Z',
    updatedAt: '2024-01-13T09:15:00Z',
    published: true,
  },
  {
    id: '4',
    userId: 'user1',
    title: 'A Foodie\'s Guide to Chengdu',
    content: 'If you love spicy food, Chengdu is your paradise! From mouth-numbing hotpot to delicious street snacks, the capital of Sichuan province offers an unforgettable culinary adventure...',
    coverImage: 'https://images.unsplash.com/photo-1552566626-52f8b828add9?w=600&h=400&fit=crop',
    tags: ['Chengdu', 'Food', 'Sichuan'],
    likes: 278,
    createdAt: '2024-01-12T14:45:00Z',
    updatedAt: '2024-01-12T14:45:00Z',
    published: true,
  },
  {
    id: '5',
    userId: 'user4',
    title: 'Suzhou: Venice of the East',
    content: 'The classical gardens of Suzhou are UNESCO World Heritage sites for a reason. Walking through the Humble Administrator\'s Garden, I felt transported to an ancient Chinese painting...',
    coverImage: 'https://images.unsplash.com/photo-1528164344705-47542687000d?w=600&h=400&fit=crop',
    tags: ['Suzhou', 'Gardens', 'UNESCO'],
    likes: 156,
    createdAt: '2024-01-11T11:20:00Z',
    updatedAt: '2024-01-11T11:20:00Z',
    published: true,
  },
  {
    id: '6',
    userId: 'user5',
    title: 'Night Markets of Taiwan',
    content: 'Taiwan\'s night markets are a sensory overload in the best way possible. From stinky tofu to bubble tea, oyster omelets to mochi, there\'s something for every adventurous eater...',
    coverImage: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&h=400&fit=crop',
    tags: ['Taiwan', 'Night Market', 'Street Food'],
    likes: 423,
    createdAt: '2024-01-10T20:00:00Z',
    updatedAt: '2024-01-10T20:00:00Z',
    published: true,
  },
]

export default function NotesPage() {
  const { user } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTag, setSelectedTag] = useState<string | null>(null)

  // User's own notes
  const myNotes = useMemo(() => {
    return mockNotes.filter(n => n.userId === user?.id).slice(0, 2)
  }, [user])

  // Get all unique tags
  const allTags = useMemo(() => {
    const tags = new Set<string>()
    mockNotes.forEach(note => {
      note.tags?.forEach(tag => tags.add(tag))
    })
    return Array.from(tags).slice(0, 10)
  }, [])

  const filteredNotes = useMemo(() => {
    let result = mockNotes

    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      result = result.filter(
        n => n.title.toLowerCase().includes(query) ||
             n.content.toLowerCase().includes(query) ||
             n.tags?.some(t => t.toLowerCase().includes(query))
      )
    }

    if (selectedTag) {
      result = result.filter(n => n.tags?.includes(selectedTag))
    }

    return result
  }, [searchQuery, selectedTag])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero section */}
      <div className="bg-gradient-to-br from-amber-500 to-orange-500 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl sm:text-5xl font-bold mb-4">Travel Stories</h1>
            <p className="text-xl text-white/80 max-w-2xl mx-auto mb-8">
              Share your adventures and discover inspiring travel stories from fellow explorers.
            </p>
            
            {/* Search bar */}
            <div className="max-w-2xl mx-auto flex gap-3">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  type="text"
                  placeholder="Search travel stories..."
                  className="w-full pl-12 pr-4 py-4 rounded-xl text-gray-900 bg-white shadow-lg focus:outline-none focus:ring-4 focus:ring-white/30 transition-all"
                />
              </div>
              <Link
                href="/notes/new"
                className="flex items-center gap-2 px-6 py-4 bg-white text-amber-600 rounded-xl font-semibold hover:shadow-lg transition-all"
              >
                <Plus className="w-5 h-5" />
                Write
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* My Notes section */}
        {myNotes.length > 0 && (
          <section className="mb-12">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">My Notes</h2>
              <Link
                href="/notes/my"
                className="text-primary-600 hover:text-primary-700 font-medium text-sm flex items-center gap-1"
              >
                View All
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                </svg>
              </Link>
            </div>

            <div className="grid sm:grid-cols-2 gap-6">
              {myNotes.map((note) => (
                <div key={note.id}>
                  <Card padding="none" hover>
                    <div className="flex">
                      {/* Image */}
                      <div className="w-1/3 aspect-square">
                        <img
                          src={note.coverImage}
                          alt={note.title}
                          className="w-full h-full object-cover rounded-l-xl"
                        />
                      </div>
                      {/* Content */}
                      <div className="flex-1 p-4 flex flex-col">
                        <h3 className="font-semibold text-gray-900 line-clamp-1 mb-2">
                          {note.title}
                        </h3>
                        <p className="text-sm text-gray-500 line-clamp-2 flex-1">
                          {note.content}
                        </p>
                        <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100">
                          <span className="text-xs text-gray-400">
                            {formatRelativeTime(note.updatedAt)}
                          </span>
                          <div className="flex gap-2">
                            <Link
                              href={`/notes/${note.id}/edit`}
                              className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"
                            >
                              <Edit3 className="w-4 h-4" />
                            </Link>
                            <button className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600">
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </Card>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Tags filter */}
        <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
          <button
            className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
              !selectedTag
                ? 'bg-amber-500 text-white shadow-md'
                : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
            }`}
            onClick={() => setSelectedTag(null)}
          >
            All
          </button>
          {allTags.map((tag) => (
            <button
              key={tag}
              className={`px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                selectedTag === tag
                  ? 'bg-amber-500 text-white shadow-md'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
              }`}
              onClick={() => setSelectedTag(tag)}
            >
              {tag}
            </button>
          ))}
        </div>

        {/* Results count */}
        <p className="text-gray-600 mb-6">
          {filteredNotes.length} stories found
        </p>

        {/* Notes grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredNotes.map((note) => (
            <Link
              key={note.id}
              href={`/notes/${note.id}`}
              className="group"
            >
              <Card padding="none" hover clickable>
                {/* Cover image */}
                <div className="relative aspect-[4/3] overflow-hidden rounded-t-xl">
                  <img
                    src={note.coverImage}
                    alt={note.title}
                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  {/* Gradient overlay */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/50 via-transparent to-transparent" />
                  {/* Tags */}
                  <div className="absolute bottom-3 left-3 flex gap-2">
                    {note.tags?.slice(0, 2).map((tag) => (
                      <Badge
                        key={tag}
                        className="bg-white/90 text-gray-700"
                        size="sm"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Content */}
                <div className="p-5">
                  {/* Title */}
                  <h3 className="text-lg font-semibold text-gray-900 group-hover:text-amber-600 transition-colors line-clamp-2 mb-2">
                    {note.title}
                  </h3>

                  {/* Excerpt */}
                  <p className="text-gray-500 text-sm line-clamp-2 mb-4">
                    {note.content}
                  </p>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                    <div className="flex items-center gap-1 text-sm text-gray-400">
                      <Clock className="w-4 h-4" />
                      {formatRelativeTime(note.createdAt)}
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1 text-sm text-gray-500">
                        <Heart className="w-4 h-4" />
                        {note.likes}
                      </span>
                    </div>
                  </div>
                </div>
              </Card>
            </Link>
          ))}
        </div>

        {/* Empty state */}
        {filteredNotes.length === 0 && (
          <div className="text-center py-16">
            <FileText className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">No stories found</h3>
            <p className="text-gray-500 mb-6">Try adjusting your search or filters</p>
            <Link
              href="/notes/new"
              className="inline-flex items-center gap-2 px-6 py-3 bg-amber-500 text-white rounded-lg font-medium hover:bg-amber-600 transition-colors"
            >
              <Plus className="w-5 h-5" />
              Write Your Story
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
