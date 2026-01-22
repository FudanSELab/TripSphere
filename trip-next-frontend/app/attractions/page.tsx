"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAttractions } from "@/lib/hooks/use-attractions";
import type { Attraction } from "@/lib/types";
import { MapPin, Search, Star, SlidersHorizontal } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

// Predefined cities with coordinates
type City = {
  name: string;
  lng: number;
  lat: number;
};

const CITIES: City[] = [
  { name: "Shanghai", lng: 121.4737, lat: 31.2304 },
  { name: "Beijing", lng: 116.4074, lat: 39.9042 },
  { name: "Guangzhou", lng: 113.2644, lat: 23.1291 },
  { name: "Shenzhen", lng: 114.0579, lat: 22.5431 },
  { name: "Hangzhou", lng: 120.1551, lat: 30.2741 },
  { name: "Chengdu", lng: 104.0668, lat: 30.5728 },
];

export default function AttractionsPage() {
  const { fetchAttractions } = useAttractions();
  const [attractions, setAttractions] = useState<Attraction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Search parameters
  const [selectedCity, setSelectedCity] = useState(CITIES[0]);
  const [searchName, setSearchName] = useState("");
  const [radiusKm, setRadiusKm] = useState(50);
  const [showFilters, setShowFilters] = useState(false);

  const loadAttractions = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchAttractions({
        location: { lng: selectedCity.lng, lat: selectedCity.lat },
        radiusKm,
        pageSize: 20,
        name: searchName.trim() || undefined,
      });
      setAttractions(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load attractions",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAttractions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <section className="from-primary-600 to-secondary-600 bg-gradient-to-br pt-32 pb-16 text-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="mb-4 text-4xl font-bold sm:text-5xl">
              Discover Amazing Attractions
            </h1>
            <p className="mx-auto max-w-2xl text-xl text-white/90">
              Explore must-see destinations with personalized recommendations
            </p>
          </div>

          {/* Search Bar */}
          <div className="mx-auto mt-8 max-w-2xl">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute top-1/2 left-3 h-5 w-5 -translate-y-1/2 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search by name..."
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") loadAttractions();
                  }}
                  className="h-12 border-0 pl-10 text-gray-900 shadow-lg"
                />
              </div>
              <Button
                onClick={loadAttractions}
                className="h-12 px-6 shadow-lg"
                disabled={loading}
              >
                <Search className="mr-2 h-5 w-5" />
                Search
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowFilters(!showFilters)}
                className="h-12 px-4 shadow-lg"
              >
                <SlidersHorizontal className="h-5 w-5" />
              </Button>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="mt-4 rounded-lg bg-white p-4 shadow-lg">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      City
                    </label>
                    <select
                      value={selectedCity.name}
                      onChange={(e) => {
                        const city =
                          CITIES.find((c) => c.name === e.target.value) ||
                          CITIES[0];
                        setSelectedCity(city);
                      }}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900"
                    >
                      {CITIES.map((city) => (
                        <option key={city.name} value={city.name}>
                          {city.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Radius: {radiusKm}km
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="100"
                      value={radiusKm}
                      onChange={(e) => setRadiusKm(Number(e.target.value))}
                      className="w-full"
                    />
                    <div className="mt-1 flex justify-between text-xs text-gray-500">
                      <span>1km</span>
                      <span>100km</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Attractions Grid */}
      <section className="py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          {/* Info Banner */}
          <div className="mb-6 rounded-lg border border-blue-200 bg-blue-50 p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-blue-100">
                <MapPin className="h-4 w-4 text-blue-600" />
              </div>
              <div className="flex-1">
                <h4 className="mb-1 font-medium text-blue-900">
                  Current Data Coverage
                </h4>
                <p className="text-sm text-blue-700">
                  Currently showing attractions in <strong>Shanghai area only</strong>. 
                  More cities will be added soon. You can still search and filter within Shanghai's 35+ attractions.
                </p>
              </div>
            </div>
          </div>

          <div className="mb-8 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">
              {searchName ? `Results for "${searchName}"` : "Popular Attractions"}
            </h2>
            {!loading && (
              <p className="text-gray-600">
                {attractions.length} attraction{attractions.length !== 1 ? "s" : ""} found
              </p>
            )}
          </div>

          {loading && (
            <div className="py-12 text-center">
              <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600"></div>
              <p className="mt-4 text-gray-600">Loading attractions...</p>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {!loading && !error && attractions.length === 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
                <MapPin className="h-8 w-8 text-gray-400" />
              </div>
              <h3 className="mb-2 text-lg font-semibold text-gray-900">
                No attractions found
              </h3>
              <p className="mb-4 text-gray-600">
                Try adjusting your search filters:
              </p>
              <ul className="mb-6 space-y-2 text-sm text-gray-500">
                <li>• Increase the search radius</li>
                <li>• Try a different city</li>
                <li>• Clear the name filter</li>
              </ul>
              <Button
                onClick={() => {
                  setSearchName("");
                  setRadiusKm(50);
                  setSelectedCity(CITIES[0]);
                  loadAttractions();
                }}
                variant="outline"
              >
                Reset Filters
              </Button>
            </div>
          )}

          {!loading && !error && attractions.length > 0 && (
            <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
              {attractions.map((attraction) => {
                // Check if image URL is valid
                const hasValidImage = !!(attraction.images && 
                  attraction.images.length > 0 && 
                  (attraction.images[0]?.startsWith('http://') || 
                   attraction.images[0]?.startsWith('https://')));
                
                return (
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
                      {hasValidImage && attraction.images ? (
                        <div className="relative h-48">
                          <Image
                            src={attraction.images[0]!}
                            alt={attraction.name}
                            fill
                            className="object-cover"
                          />
                          {attraction.rating && (
                            <div className="absolute top-4 right-4">
                              <Badge
                                variant="default"
                                className="bg-white text-gray-900 shadow-lg"
                              >
                                <Star className="mr-1 h-3 w-3 fill-yellow-400 text-yellow-400" />
                                {attraction.rating}
                              </Badge>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="relative h-48 bg-gradient-to-br from-primary-100 to-secondary-100 flex items-center justify-center">
                          <MapPin className="h-16 w-16 text-primary-300" />
                          {attraction.rating && (
                            <div className="absolute top-4 right-4">
                              <Badge
                                variant="default"
                                className="bg-white text-gray-900 shadow-lg"
                              >
                                <Star className="mr-1 h-3 w-3 fill-yellow-400 text-yellow-400" />
                                {attraction.rating}
                              </Badge>
                            </div>
                          )}
                        </div>
                      )}

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
                          <div className="flex flex-wrap gap-2">
                            {attraction.tags.slice(0, 3).map((tag) => (
                              <Badge key={tag} variant="secondary" size="sm">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </Card>
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
