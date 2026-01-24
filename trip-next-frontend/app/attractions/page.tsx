"use client";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { useAttractions } from "@/hooks/use-attractions";
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
    <div className="bg-muted min-h-screen">
      {/* Hero Section */}
      <section className="bg-primary text-primary-foreground pt-16 pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Discover Amazing Attractions
            </h1>
            <p className="text-primary-foreground/90 mx-auto max-w-2xl text-xl">
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
            <h2 className="text-foreground text-2xl font-bold">
              Popular Attractions
            </h2>
            <p className="text-muted-foreground">
              {attractions.length} attractions found
            </p>
          </div>

          {loading ? (
            <div className="py-12 text-center">
              <p className="text-muted-foreground">Loading attractions...</p>
            </div>
          ) : attractions.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-muted-foreground">
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
                  <Card className="h-full overflow-hidden">
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
                        <div className="bg-muted flex h-full items-center justify-center">
                          <MapPin className="text-muted-foreground h-12 w-12" />
                        </div>
                      )}
                      <div className="absolute top-4 right-4">
                        <Badge
                          variant="default"
                          className="bg-background text-foreground shadow-lg"
                        >
                          <Star className="fill-chart-4 text-chart-4 mr-1 h-3 w-3" />
                          {attraction.rating?.toFixed(1)}
                        </Badge>
                      </div>
                    </div>

                    <div className="p-5">
                      <div className="mb-2 flex items-start justify-between">
                        <div>
                          <h3 className="text-foreground mb-1 text-xl font-semibold">
                            {attraction.name}
                          </h3>
                          <div className="text-muted-foreground flex items-center gap-1 text-sm">
                            <MapPin className="h-4 w-4" />
                            {attraction.address.city},{" "}
                            {attraction.address.country}
                          </div>
                        </div>
                      </div>

                      <p className="text-muted-foreground mb-4 line-clamp-2 text-sm">
                        {attraction.description}
                      </p>

                      {attraction.tags && attraction.tags.length > 0 && (
                        <div className="mb-4 flex flex-wrap gap-2">
                          {attraction.tags?.slice(0, 3).map((tag, index) => (
                            <Badge
                              key={`${attraction.id}-tag-${index}`}
                              variant="secondary"
                            >
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}

                      <div className="border-border text-muted-foreground flex items-center gap-4 border-t pt-4 text-sm">
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
