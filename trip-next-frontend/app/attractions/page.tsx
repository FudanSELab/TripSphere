"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Clock, DollarSign, MapPin, Star } from "lucide-react";
import Image from "next/image";
import Link from "next/link";

// Mock data - in production, this would come from API
const attractions = [
  {
    id: "1",
    name: "The Bund",
    description:
      "The Bund is a waterfront area in central Shanghai, featuring a mix of historical colonial-era buildings and modern skyscrapers.",
    city: "Shanghai",
    country: "China",
    rating: 4.8,
    category: "Landmark",
    openingHours: "24 hours",
    ticketPrice: "Free",
    image:
      "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=600&h=400&fit=crop",
    tags: ["Historic", "Scenic", "Night View", "Photography"],
  },
  {
    id: "2",
    name: "Yu Garden",
    description:
      "A classical Chinese garden located in the Old City of Shanghai, featuring traditional architecture and landscapes.",
    city: "Shanghai",
    country: "China",
    rating: 4.6,
    category: "Garden",
    openingHours: "8:30 AM - 5:00 PM",
    ticketPrice: "¥40",
    image:
      "https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=600&h=400&fit=crop",
    tags: ["Traditional", "Cultural", "Architecture"],
  },
  {
    id: "3",
    name: "Oriental Pearl Tower",
    description:
      "An iconic TV tower and landmark of Shanghai with observation decks offering panoramic views of the city.",
    city: "Shanghai",
    country: "China",
    rating: 4.5,
    category: "Landmark",
    openingHours: "9:00 AM - 9:00 PM",
    ticketPrice: "¥160",
    image:
      "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=600&h=400&fit=crop",
    tags: ["Modern", "Viewpoint", "Landmark"],
  },
  {
    id: "4",
    name: "Forbidden City",
    description:
      "The Chinese imperial palace from the Ming dynasty to the end of the Qing dynasty, now a museum.",
    city: "Beijing",
    country: "China",
    rating: 4.9,
    category: "Historical",
    openingHours: "8:30 AM - 5:00 PM",
    ticketPrice: "¥60",
    image:
      "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=600&h=400&fit=crop",
    tags: ["Historical", "Cultural", "UNESCO"],
  },
  {
    id: "5",
    name: "West Lake",
    description:
      "A UNESCO World Heritage Site featuring beautiful scenery, gardens, and traditional pagodas.",
    city: "Hangzhou",
    country: "China",
    rating: 4.7,
    category: "Nature",
    openingHours: "24 hours",
    ticketPrice: "Free",
    image:
      "https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=600&h=400&fit=crop",
    tags: ["Nature", "Scenic", "UNESCO"],
  },
  {
    id: "6",
    name: "The Humble Administrator's Garden",
    description:
      "One of the most famous classical gardens in Suzhou, representing traditional Chinese garden design.",
    city: "Suzhou",
    country: "China",
    rating: 4.6,
    category: "Garden",
    openingHours: "7:30 AM - 5:30 PM",
    ticketPrice: "¥70",
    image:
      "https://images.unsplash.com/photo-1528164344705-47542687000d?w=600&h=400&fit=crop",
    tags: ["Garden", "Historical", "UNESCO"],
  },
];

export default function AttractionsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="from-primary-600 to-secondary-600 bg-linear-to-br py-16 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Discover Amazing Attractions
            </h1>
            <p className="mx-auto max-w-2xl text-xl text-white/90">
              Explore thousands of must-see destinations around the world with
              personalized recommendations
            </p>
          </div>
        </div>
      </section>

      {/* Attractions Grid */}
      <section className="py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-8 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">
              Popular Attractions
            </h2>
            <p className="text-gray-600">
              {attractions.length} attractions found
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {attractions.map((attraction, index) => (
              <Link key={attraction.id} href={`/attractions/${attraction.id}`}>
                <Card
                  hover
                  clickable
                  padding="none"
                  className="h-full overflow-hidden"
                >
                  <div className="relative h-48">
                    <Image
                      src={attraction.image}
                      alt={attraction.name}
                      fill
                      className="object-cover"
                    />
                    <div className="absolute top-4 right-4">
                      <Badge
                        variant="default"
                        className="bg-white text-gray-900 shadow-lg"
                      >
                        <Star className="mr-1 h-3 w-3 fill-yellow-400 text-yellow-400" />
                        {attraction.rating}
                      </Badge>
                    </div>
                  </div>

                  <div className="p-5">
                    <div className="mb-2 flex items-start justify-between">
                      <div>
                        <h3 className="mb-1 text-xl font-semibold text-gray-900">
                          {attraction.name}
                        </h3>
                        <div className="flex items-center gap-1 text-sm text-gray-500">
                          <MapPin className="h-4 w-4" />
                          {attraction.city}, {attraction.country}
                        </div>
                      </div>
                    </div>

                    <p className="mb-4 line-clamp-2 text-sm text-gray-600">
                      {attraction.description}
                    </p>

                    <div className="mb-4 flex flex-wrap gap-2">
                      {attraction.tags.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="secondary" size="sm">
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    <div className="flex items-center gap-4 border-t border-gray-100 pt-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {attraction.openingHours}
                      </div>
                      <div className="flex items-center gap-1">
                        <DollarSign className="h-4 w-4" />
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
  );
}
