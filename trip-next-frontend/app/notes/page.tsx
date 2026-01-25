"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/lib/hooks/use-auth";
import type { Note } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";
import {
  Clock,
  Edit3,
  FileText,
  Heart,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

// Mock notes data
const mockNotes: Note[] = [
  {
    id: "1",
    userId: "user1",
    title: "Amazing Weekend in Shanghai",
    content:
      "My trip to Shanghai was absolutely incredible! From the historic Bund to the modern Pudong skyline, every moment was memorable. The food was exceptional, especially the xiaolongbao at Din Tai Fung...",
    coverImage:
      "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&h=400&fit=crop",
    tags: ["Shanghai", "City Trip", "Food"],
    likes: 245,
    createdAt: "2024-01-15T10:00:00Z",
    updatedAt: "2024-01-15T10:00:00Z",
    published: true,
  },
  {
    id: "2",
    userId: "user2",
    title: "West Lake: A Photographer's Paradise",
    content:
      "As a photographer, West Lake in Hangzhou has always been on my bucket list. The misty mornings, traditional pagodas, and serene waters create the perfect backdrop for stunning photos...",
    coverImage:
      "https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=600&h=400&fit=crop",
    tags: ["Hangzhou", "Photography", "Nature"],
    likes: 189,
    createdAt: "2024-01-14T15:30:00Z",
    updatedAt: "2024-01-14T15:30:00Z",
    published: true,
  },
  {
    id: "3",
    userId: "user3",
    title: "Hidden Gems of Beijing Hutongs",
    content:
      "Wandering through Beijing's ancient hutongs was like stepping back in time. The narrow alleyways are filled with history, local eateries, and charming courtyard homes that tell stories of old Beijing...",
    coverImage:
      "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600&h=400&fit=crop",
    tags: ["Beijing", "Culture", "History"],
    likes: 312,
    createdAt: "2024-01-13T09:15:00Z",
    updatedAt: "2024-01-13T09:15:00Z",
    published: true,
  },
  {
    id: "4",
    userId: "user1",
    title: "A Foodie's Guide to Chengdu",
    content:
      "If you love spicy food, Chengdu is your paradise! From mouth-numbing hotpot to delicious street snacks, the capital of Sichuan province offers an unforgettable culinary adventure...",
    coverImage:
      "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=600&h=400&fit=crop",
    tags: ["Chengdu", "Food", "Sichuan"],
    likes: 278,
    createdAt: "2024-01-12T14:45:00Z",
    updatedAt: "2024-01-12T14:45:00Z",
    published: true,
  },
  {
    id: "5",
    userId: "user4",
    title: "Suzhou: Venice of the East",
    content:
      "The classical gardens of Suzhou are UNESCO World Heritage sites for a reason. Walking through the Humble Administrator's Garden, I felt transported to an ancient Chinese painting...",
    coverImage:
      "https://images.unsplash.com/photo-1528164344705-47542687000d?w=600&h=400&fit=crop",
    tags: ["Suzhou", "Gardens", "UNESCO"],
    likes: 156,
    createdAt: "2024-01-11T11:20:00Z",
    updatedAt: "2024-01-11T11:20:00Z",
    published: true,
  },
  {
    id: "6",
    userId: "user5",
    title: "Night Markets of Taiwan",
    content:
      "Taiwan's night markets are a sensory overload in the best way possible. From stinky tofu to bubble tea, oyster omelets to mochi, there's something for every adventurous eater...",
    coverImage:
      "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600&h=400&fit=crop",
    tags: ["Taiwan", "Night Market", "Street Food"],
    likes: 423,
    createdAt: "2024-01-10T20:00:00Z",
    updatedAt: "2024-01-10T20:00:00Z",
    published: true,
  },
];

export default function NotesPage() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState<string | null>(null);

  // User's own notes
  const myNotes = useMemo(() => {
    return mockNotes.filter((n) => n.userId === user?.id).slice(0, 2);
  }, [user]);

  // Get all unique tags
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    mockNotes.forEach((note) => {
      note.tags?.forEach((tag) => tags.add(tag));
    });
    return Array.from(tags).slice(0, 10);
  }, []);

  const filteredNotes = useMemo(() => {
    let result = mockNotes;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (n) =>
          n.title.toLowerCase().includes(query) ||
          n.content.toLowerCase().includes(query) ||
          n.tags?.some((t) => t.toLowerCase().includes(query)),
      );
    }

    if (selectedTag) {
      result = result.filter((n) => n.tags?.includes(selectedTag));
    }

    return result;
  }, [searchQuery, selectedTag]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero section */}
      <div className="bg-linear-to-br from-amber-500 to-orange-500 pt-16 pb-16 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Travel Stories
            </h1>
            <p className="mx-auto mb-8 max-w-2xl text-xl text-white/80">
              Share your adventures and discover inspiring travel stories from
              fellow explorers.
            </p>

            {/* Search bar */}
            <div className="mx-auto flex max-w-2xl gap-3">
              <div className="relative flex-1">
                <Search className="absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2 text-gray-400" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  type="text"
                  placeholder="Search travel stories..."
                  className="w-full rounded-xl bg-white py-4 pr-4 pl-12 text-gray-900 shadow-lg transition-all focus:ring-4 focus:ring-white/30 focus:outline-none"
                />
              </div>
              <Link
                href="/notes/new"
                className="flex items-center gap-2 rounded-xl bg-white px-6 py-4 font-semibold text-amber-600 transition-all hover:shadow-lg"
              >
                <Plus className="h-5 w-5" />
                Write
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* My Notes section */}
        {myNotes.length > 0 && (
          <section className="mb-12">
            <div className="mb-6 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">My Notes</h2>
              <Link
                href="/notes/my"
                className="text-primary-600 hover:text-primary-700 flex items-center gap-1 text-sm font-medium"
              >
                View All
                <svg
                  className="h-4 w-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </Link>
            </div>

            <div className="grid gap-6 sm:grid-cols-2">
              {myNotes.map((note) => (
                <div key={note.id}>
                  <Card padding="none" hover>
                    <div className="flex">
                      {/* Image */}
                      <div className="aspect-square w-1/3">
                        <img
                          src={note.coverImage}
                          alt={note.title}
                          className="h-full w-full rounded-l-xl object-cover"
                        />
                      </div>
                      {/* Content */}
                      <div className="flex flex-1 flex-col p-4">
                        <h3 className="mb-2 line-clamp-1 font-semibold text-gray-900">
                          {note.title}
                        </h3>
                        <p className="line-clamp-2 flex-1 text-sm text-gray-500">
                          {note.content}
                        </p>
                        <div className="mt-3 flex items-center justify-between border-t border-gray-100 pt-3">
                          <span className="text-xs text-gray-400">
                            {formatRelativeTime(note.updatedAt)}
                          </span>
                          <div className="flex gap-2">
                            <Link
                              href={`/notes/${note.id}/edit`}
                              className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                            >
                              <Edit3 className="h-4 w-4" />
                            </Link>
                            <button className="rounded-lg p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600">
                              <Trash2 className="h-4 w-4" />
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
        <div className="mb-8 flex items-center gap-2 overflow-x-auto pb-2">
          <button
            className={`rounded-full px-4 py-2 text-sm font-medium whitespace-nowrap transition-all ${
              !selectedTag
                ? "bg-amber-500 text-white shadow-md"
                : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-100"
            }`}
            onClick={() => setSelectedTag(null)}
          >
            All
          </button>
          {allTags.map((tag) => (
            <button
              key={tag}
              className={`rounded-full px-4 py-2 text-sm font-medium whitespace-nowrap transition-all ${
                selectedTag === tag
                  ? "bg-amber-500 text-white shadow-md"
                  : "border border-gray-200 bg-white text-gray-700 hover:bg-gray-100"
              }`}
              onClick={() => setSelectedTag(tag)}
            >
              {tag}
            </button>
          ))}
        </div>

        {/* Results count */}
        <p className="mb-6 text-gray-600">
          {filteredNotes.length} stories found
        </p>

        {/* Notes grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredNotes.map((note) => (
            <Link key={note.id} href={`/notes/${note.id}`} className="group">
              <Card padding="none" hover clickable>
                {/* Cover image */}
                <div className="relative aspect-4/3 overflow-hidden rounded-t-xl">
                  <img
                    src={note.coverImage}
                    alt={note.title}
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  {/* Gradient overlay */}
                  <div className="absolute inset-0 bg-linear-to-t from-black/50 via-transparent to-transparent" />
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
                  <h3 className="mb-2 line-clamp-2 text-lg font-semibold text-gray-900 transition-colors group-hover:text-amber-600">
                    {note.title}
                  </h3>

                  {/* Excerpt */}
                  <p className="mb-4 line-clamp-2 text-sm text-gray-500">
                    {note.content}
                  </p>

                  {/* Footer */}
                  <div className="flex items-center justify-between border-t border-gray-100 pt-4">
                    <div className="flex items-center gap-1 text-sm text-gray-400">
                      <Clock className="h-4 w-4" />
                      {formatRelativeTime(note.createdAt)}
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1 text-sm text-gray-500">
                        <Heart className="h-4 w-4" />
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
          <div className="py-16 text-center">
            <FileText className="mx-auto mb-4 h-16 w-16 text-gray-300" />
            <h3 className="mb-2 text-xl font-semibold text-gray-900">
              No stories found
            </h3>
            <p className="mb-6 text-gray-500">
              Try adjusting your search or filters
            </p>
            <Link
              href="/notes/new"
              className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-6 py-3 font-medium text-white transition-colors hover:bg-amber-600"
            >
              <Plus className="h-5 w-5" />
              Write Your Story
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
