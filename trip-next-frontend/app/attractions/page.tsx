"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useAttractions } from "@/lib/hooks/use-attractions";
import type { Attraction } from "@/lib/types";
import { Clock, MapPin, Star, Ticket } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

export default function AttractionsPage() {
  const { fetchAttractionsNearby } = useAttractions();
  const [attractions, setAttractions] = useState<Attraction[]>([]);
  const [loading, setLoading] = useState(true);

  // Load attractions on mount
  useEffect(() => {
    const loadAttractions = async () => {
      try {
        const data = await fetchAttractionsNearby({
          location: {
            latitude: 31.2304, // Default: Shanghai
            longitude: 121.4737,
          },
          radiusKm: 50, // 50km radius
        });
        setAttractions(data);
      } catch (error) {
        console.error("Error loading attractions:", error);
      } finally {
        setLoading(false);
      }
    };

    loadAttractions();
  }, []);
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="from-primary-600 to-secondary-600 bg-linear-to-br pt-16 pb-16 text-white">
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

          {loading ? (
            <div className="py-12 text-center">
              <p className="text-gray-500">Loading attractions...</p>
            </div>
          ) : attractions.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-gray-500">
                No attractions found in this area. Try adjusting the search
                radius or location.
              </p>
            </div>
          ) : (
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {attractions.map((attraction) => (
                <Link
                  key={attraction.id}
                  href={`/attractions/${attraction.id}`}
                >
                  <Card
                    hover
                    clickable
                    padding="none"
                    className="h-full overflow-hidden"
                  >
                    <div className="relative h-48">
                      {attraction.images && attraction.images.length > 0 ? (
                        <Image
                          src={attraction.images[0]}
                          alt={attraction.name}
                          fill
                          className="object-cover"
                          unoptimized
                        />
                      ) : (
                        <div className="flex h-full items-center justify-center bg-gray-200">
                          <MapPin className="h-12 w-12 text-gray-400" />
                        </div>
                      )}
                      <div className="absolute top-4 right-4">
                        <Badge
                          variant="default"
                          className="bg-white text-gray-900 shadow-lg"
                        >
                          <Star className="mr-1 h-3 w-3 fill-yellow-400 text-yellow-400" />
                          {attraction.rating?.toFixed(1)}
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
                            {attraction.address.city},{" "}
                            {attraction.address.country}
                          </div>
                        </div>
                      </div>

                      <p className="mb-4 line-clamp-2 text-sm text-gray-600">
                        {attraction.description}
                      </p>

                      {attraction.tags && attraction.tags.length > 0 && (
                        <div className="mb-4 flex flex-wrap gap-2">
                          {attraction.tags?.slice(0, 3).map((tag, index) => (
                            <Badge
                              key={`${attraction.id}-tag-${index}`}
                              variant="secondary"
                              size="sm"
                            >
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}

                      <div className="flex items-center gap-4 border-t border-gray-100 pt-4 text-sm text-gray-500">
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4" />
                          <span className="line-clamp-1">
                            {attraction.openingHours}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Ticket className="h-4 w-4" />
                          {attraction.ticketPrice}
                        </div>
                      </div>
                    </div>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
