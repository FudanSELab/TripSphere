"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import type { Hotel as HotelType } from "@/lib/types";
import {
  ChevronDown,
  Filter,
  Heart,
  Hotel,
  MapPin,
  Search,
  Star,
} from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

// Mock data for hotels
const mockHotels: HotelType[] = [
  {
    id: "1",
    name: "The Peninsula Shanghai",
    address: {
      country: "China",
      province: "Shanghai",
      city: "Shanghai",
      county: "Huangpu",
      district: "",
      street: "No. 32 Zhongshan East 1st Road",
    },
    introduction:
      "A luxurious 5-star hotel overlooking the historic Bund and the modern Pudong skyline.",
    tags: ["Luxury", "5-Star", "River View", "Spa", "Restaurant"],
    rooms: [
      {
        name: "Deluxe Room",
        totalNumber: 50,
        remainingNumber: 10,
        bedWidth: 2.0,
        bedNumber: 1,
        minArea: 55,
        maxArea: 60,
        peopleNumber: 2,
        tags: ["City View"],
      },
      {
        name: "Premier Suite",
        totalNumber: 20,
        remainingNumber: 5,
        bedWidth: 2.0,
        bedNumber: 1,
        minArea: 88,
        maxArea: 95,
        peopleNumber: 2,
        tags: ["River View", "Living Room"],
      },
    ],
    location: { lng: 121.4883, lat: 31.2365 },
    rating: 4.9,
    priceRange: "¥3,500 - ¥15,000",
    images: [
      "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&h=400&fit=crop",
    ],
  },
  {
    id: "2",
    name: "Hyatt on the Bund",
    address: {
      country: "China",
      province: "Shanghai",
      city: "Shanghai",
      county: "Hongkou",
      district: "",
      street: "No. 199 Huangpu Road",
    },
    introduction:
      "Modern luxury hotel with stunning views of the Huangpu River and city skyline.",
    tags: ["Business", "5-Star", "River View", "Pool", "Gym"],
    rooms: [
      {
        name: "Grand Room",
        totalNumber: 80,
        remainingNumber: 25,
        bedWidth: 1.8,
        bedNumber: 1,
        minArea: 40,
        maxArea: 45,
        peopleNumber: 2,
        tags: ["City View"],
      },
      {
        name: "River View Suite",
        totalNumber: 30,
        remainingNumber: 8,
        bedWidth: 2.0,
        bedNumber: 1,
        minArea: 65,
        maxArea: 75,
        peopleNumber: 2,
        tags: ["River View"],
      },
    ],
    location: { lng: 121.4928, lat: 31.2456 },
    rating: 4.7,
    priceRange: "¥1,800 - ¥6,500",
    images: [
      "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&h=400&fit=crop",
    ],
  },
  {
    id: "3",
    name: "Mandarin Oriental Pudong",
    address: {
      country: "China",
      province: "Shanghai",
      city: "Shanghai",
      county: "Pudong",
      district: "",
      street: "No. 111 Pudong South Road",
    },
    introduction:
      "Elegant hotel in the heart of Lujiazui financial district with world-class amenities.",
    tags: ["Luxury", "5-Star", "Spa", "Fine Dining", "Business Center"],
    rooms: [
      {
        name: "Superior Room",
        totalNumber: 100,
        remainingNumber: 30,
        bedWidth: 1.8,
        bedNumber: 1,
        minArea: 45,
        maxArea: 50,
        peopleNumber: 2,
        tags: ["City View"],
      },
      {
        name: "Club Suite",
        totalNumber: 25,
        remainingNumber: 7,
        bedWidth: 2.0,
        bedNumber: 1,
        minArea: 80,
        maxArea: 90,
        peopleNumber: 2,
        tags: ["Club Access", "River View"],
      },
    ],
    location: { lng: 121.5032, lat: 31.2308 },
    rating: 4.8,
    priceRange: "¥2,500 - ¥12,000",
    images: [
      "https://images.unsplash.com/photo-1571003123894-1f0594d2b5d9?w=600&h=400&fit=crop",
    ],
  },
  {
    id: "4",
    name: "Four Seasons Hangzhou",
    address: {
      country: "China",
      province: "Zhejiang",
      city: "Hangzhou",
      county: "",
      district: "",
      street: "No. 5 Lingyin Road",
    },
    introduction:
      "A tranquil retreat nestled beside West Lake with traditional Chinese architecture.",
    tags: ["Resort", "5-Star", "Lake View", "Spa", "Garden"],
    rooms: [
      {
        name: "Garden View Room",
        totalNumber: 60,
        remainingNumber: 15,
        bedWidth: 1.8,
        bedNumber: 1,
        minArea: 50,
        maxArea: 55,
        peopleNumber: 2,
        tags: ["Garden View"],
      },
      {
        name: "West Lake Suite",
        totalNumber: 15,
        remainingNumber: 3,
        bedWidth: 2.0,
        bedNumber: 1,
        minArea: 100,
        maxArea: 120,
        peopleNumber: 2,
        tags: ["Lake View", "Balcony"],
      },
    ],
    location: { lng: 120.1285, lat: 30.2521 },
    rating: 4.9,
    priceRange: "¥3,200 - ¥18,000",
    images: [
      "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=600&h=400&fit=crop",
    ],
  },
  {
    id: "5",
    name: "Waldorf Astoria Beijing",
    address: {
      country: "China",
      province: "Beijing",
      city: "Beijing",
      county: "Dongcheng",
      district: "",
      street: "No. 5-15 Jinyu Hutong",
    },
    introduction:
      "Historic Art Deco hotel offering exceptional service in the heart of Beijing.",
    tags: ["Historic", "5-Star", "Central Location", "Restaurant", "Bar"],
    rooms: [
      {
        name: "Deluxe King",
        totalNumber: 70,
        remainingNumber: 20,
        bedWidth: 2.0,
        bedNumber: 1,
        minArea: 52,
        maxArea: 58,
        peopleNumber: 2,
        tags: ["City View"],
      },
      {
        name: "Hutong Suite",
        totalNumber: 12,
        remainingNumber: 2,
        bedWidth: 2.0,
        bedNumber: 1,
        minArea: 110,
        maxArea: 130,
        peopleNumber: 2,
        tags: ["Hutong View", "Living Room"],
      },
    ],
    location: { lng: 116.4142, lat: 39.9149 },
    rating: 4.8,
    priceRange: "¥2,800 - ¥20,000",
    images: [
      "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600&h=400&fit=crop",
    ],
  },
];

const categories = ["All", "Luxury", "Business", "Resort", "Historic"];

export default function HotelsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const filteredHotels = useMemo(() => {
    let result = mockHotels;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (h) =>
          h.name.toLowerCase().includes(query) ||
          h.introduction.toLowerCase().includes(query) ||
          h.address.city.toLowerCase().includes(query) ||
          h.tags?.some((t) => t.toLowerCase().includes(query)),
      );
    }

    if (selectedCategory && selectedCategory !== "All") {
      result = result.filter((h) => h.tags?.includes(selectedCategory));
    }

    return result;
  }, [searchQuery, selectedCategory]);

  const selectCategory = (category: string) => {
    setSelectedCategory(category === "All" ? null : category);
  };

  const getLowestPrice = (hotel: HotelType) => {
    return hotel.priceRange?.split(" - ")[0] || "N/A";
  };

  return (
    <div className="bg-muted min-h-screen">
      {/* Hero section */}
      <div className="bg-primary text-primary-foreground pt-16 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Find Your Perfect Stay
            </h1>
            <p className="text-primary-foreground/80 mx-auto mb-8 max-w-2xl text-xl">
              Discover handpicked hotels with AI-powered recommendations for
              your ideal trip.
            </p>

            {/* Search bar */}
            <div className="mx-auto max-w-2xl">
              <div className="relative">
                <Search className="text-muted-foreground absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  type="text"
                  placeholder="Search hotels, cities, or amenities..."
                  className="bg-background text-foreground focus:ring-ring/30 w-full rounded-xl py-4 pr-4 pl-12 shadow-lg transition-all focus:ring-4 focus:outline-none"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Filters */}
        <div className="mb-8 flex items-center justify-between">
          {/* Categories */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2">
            {categories.map((category) => (
              <button
                key={category}
                className={`rounded-full px-4 py-2 text-sm font-medium whitespace-nowrap transition-all ${
                  (category === "All" && !selectedCategory) ||
                  selectedCategory === category
                    ? "bg-primary text-primary-foreground shadow-md"
                    : "border-border bg-background text-foreground hover:bg-muted border"
                }`}
                onClick={() => selectCategory(category)}
              >
                {category}
              </button>
            ))}
          </div>

          {/* Filter button */}
          <button
            className="border-border bg-background text-foreground hover:bg-muted flex items-center gap-2 rounded-lg border px-4 py-2 transition-colors"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4" />
            Filters
            <ChevronDown
              className={`h-4 w-4 transition-transform ${showFilters ? "rotate-180" : ""}`}
            />
          </button>
        </div>

        {/* Results count */}
        <p className="text-muted-foreground mb-6">
          {filteredHotels.length} hotels found
        </p>

        {/* Hotels grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredHotels.map((hotel) => (
            <Link key={hotel.id} href={`/hotels/${hotel.id}`} className="group">
              <Card>
                {/* Image */}
                <div className="relative aspect-4/3 overflow-hidden rounded-t-xl">
                  <img
                    src={hotel.images?.[0]}
                    alt={hotel.name}
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  {/* Overlay badges */}
                  <div className="absolute top-3 left-3 flex gap-2">
                    <Badge variant="secondary">{hotel.tags?.[0]}</Badge>
                  </div>
                  {/* Like button */}
                  <button
                    className="bg-background/90 text-muted-foreground hover:bg-background hover:text-destructive absolute top-3 right-3 flex h-9 w-9 items-center justify-center rounded-full transition-all"
                    onClick={(e) => e.preventDefault()}
                  >
                    <Heart className="h-5 w-5" />
                  </button>
                  {/* Price badge */}
                  <div className="bg-background/95 absolute right-3 bottom-3 rounded-lg px-3 py-1.5 shadow-lg">
                    <span className="text-primary text-sm font-bold">
                      From {getLowestPrice(hotel)}
                    </span>
                    <span className="text-muted-foreground text-xs">
                      /night
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-5">
                  {/* Title and rating */}
                  <div className="mb-2 flex items-start justify-between gap-2">
                    <h3 className="text-foreground group-hover:text-primary text-lg font-semibold transition-colors">
                      {hotel.name}
                    </h3>
                    <div className="text-chart-4 flex items-center gap-1">
                      <Star className="h-4 w-4 fill-current" />
                      <span className="text-foreground text-sm font-medium">
                        {hotel.rating}
                      </span>
                    </div>
                  </div>

                  {/* Location */}
                  <p className="text-muted-foreground mb-3 flex items-center gap-1 text-sm">
                    <MapPin className="h-4 w-4" />
                    {hotel.address.city}, {hotel.address.country}
                  </p>

                  {/* Description */}
                  <p className="text-muted-foreground mb-4 line-clamp-2 text-sm">
                    {hotel.introduction}
                  </p>

                  {/* Tags */}
                  <div className="mb-4 flex flex-wrap gap-2">
                    {hotel.tags?.slice(1, 4).map((tag) => (
                      <Badge key={tag} variant="outline">
                        {tag}
                      </Badge>
                    ))}
                  </div>

                  {/* Room info */}
                  <div className="border-border flex items-center justify-between border-t pt-4">
                    <div className="text-muted-foreground text-sm">
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
          <div className="py-16 text-center">
            <Hotel className="text-muted-foreground/30 mx-auto mb-4 h-16 w-16" />
            <h3 className="text-foreground mb-2 text-xl font-semibold">
              No hotels found
            </h3>
            <p className="text-muted-foreground">
              Try adjusting your search or filters
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
