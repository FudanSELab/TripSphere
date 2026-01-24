"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";
import type { Note } from "@/lib/types";
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
    <div className="bg-muted min-h-screen">
      {/* Hero section */}
      <div className="bg-primary text-primary-foreground pt-16 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Travel Stories
            </h1>
            <p className="text-primary-foreground/80 mx-auto mb-8 max-w-2xl text-xl">
              Share your adventures and discover inspiring travel stories from
              fellow explorers.
            </p>

            {/* Search bar */}
            <div className="mx-auto flex max-w-2xl gap-3">
              <div className="relative flex-1">
                <Search className="text-muted-foreground absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  type="text"
                  placeholder="Search travel stories..."
                  className="bg-background text-foreground focus:ring-ring/30 w-full rounded-xl py-4 pr-4 pl-12 shadow-lg transition-all focus:ring-4 focus:outline-none"
                />
              </div>
              <Link
                href="/notes/new"
                className="bg-background text-primary flex items-center gap-2 rounded-xl px-6 py-4 font-semibold transition-all hover:shadow-lg"
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
              <h2 className="text-foreground text-2xl font-bold">My Notes</h2>
              <Link
                href="/notes/my"
                className="text-primary hover:text-primary/80 flex items-center gap-1 text-sm font-medium"
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
                  <Card>
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
                        <h3 className="text-foreground mb-2 line-clamp-1 font-semibold">
                          {note.title}
                        </h3>
                        <p className="text-muted-foreground line-clamp-2 flex-1 text-sm">
                          {note.content}
                        </p>
                        <div className="border-border mt-3 flex items-center justify-between border-t pt-3">
                          <span className="text-muted-foreground text-xs">
                            {note.updatedAt}
                          </span>
                          <div className="flex gap-2">
                            <Link
                              href={`/notes/${note.id}/edit`}
                              className="text-muted-foreground hover:bg-muted hover:text-foreground rounded-lg p-1.5"
                            >
                              <Edit3 className="h-4 w-4" />
                            </Link>
                            <button className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive rounded-lg p-1.5">
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
                ? "bg-primary text-primary-foreground shadow-md"
                : "border-border bg-background text-foreground hover:bg-muted border"
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
                  ? "bg-primary text-primary-foreground shadow-md"
                  : "border-border bg-background text-foreground hover:bg-muted border"
              }`}
              onClick={() => setSelectedTag(tag)}
            >
              {tag}
            </button>
          ))}
        </div>

        {/* Results count */}
        <p className="text-muted-foreground mb-6">
          {filteredNotes.length} stories found
        </p>

        {/* Notes grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredNotes.map((note) => (
            <Link key={note.id} href={`/notes/${note.id}`} className="group">
              <Card>
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
                        className="bg-background/90 text-foreground"
                      >
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Content */}
                <div className="p-5">
                  {/* Title */}
                  <h3 className="text-foreground group-hover:text-primary mb-2 line-clamp-2 text-lg font-semibold transition-colors">
                    {note.title}
                  </h3>

                  {/* Excerpt */}
                  <p className="text-muted-foreground mb-4 line-clamp-2 text-sm">
                    {note.content}
                  </p>

                  {/* Footer */}
                  <div className="border-border flex items-center justify-between border-t pt-4">
                    <div className="text-muted-foreground flex items-center gap-1 text-sm">
                      <Clock className="h-4 w-4" />
                      {note.createdAt}
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-muted-foreground flex items-center gap-1 text-sm">
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
            <FileText className="text-muted-foreground/30 mx-auto mb-4 h-16 w-16" />
            <h3 className="text-foreground mb-2 text-xl font-semibold">
              No stories found
            </h3>
            <p className="text-muted-foreground mb-6">
              Try adjusting your search or filters
            </p>
            <Link
              href="/notes/new"
              className="bg-primary text-primary-foreground hover:bg-primary/90 inline-flex items-center gap-2 rounded-lg px-6 py-3 font-medium transition-colors"
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
