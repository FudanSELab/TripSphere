"use client";

import { Card } from "@/components/ui/card";
import { ImageCarousel } from "@/components/ui/image-carousel";
import {
  ArrowRight,
  Calendar,
  FileText,
  Globe,
  Hotel,
  MapPin,
  MessageSquare,
  Sparkles,
  Star,
  Users,
  Zap,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";

const heroImages = [
  {
    src: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1200&h=900&fit=crop",
    alt: "Mountain landscape at sunset",
    title: "Discover Natural Wonders",
  },
  {
    src: "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1200&h=900&fit=crop",
    alt: "Paris Eiffel Tower",
    title: "Explore Iconic Cities",
  },
  {
    src: "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=1200&h=900&fit=crop",
    alt: "Tropical beach paradise",
    title: "Relax on Beautiful Beaches",
  },
  {
    src: "https://images.unsplash.com/photo-1464817739973-0128fe77aaa1?w=1200&h=900&fit=crop",
    alt: "Mountain valley with lake",
    title: "Experience Adventure",
  },
  {
    src: "https://images.unsplash.com/photo-1513415564515-763d91423bdd?w=1200&h=900&fit=crop",
    alt: "Ancient temple architecture",
    title: "Immerse in Culture",
  },
];

const features = [
  {
    icon: MapPin,
    title: "Discover Attractions",
    description:
      "Explore thousands of attractions with AI-powered recommendations tailored to your interests.",
  },
  {
    icon: Hotel,
    title: "Find Perfect Hotels",
    description:
      "Get personalized hotel recommendations based on your preferences, budget, and travel style.",
  },
  {
    icon: Calendar,
    title: "Smart Itinerary Planning",
    description:
      "Let our AI create optimized travel itineraries with intelligent route planning.",
  },
  {
    icon: MessageSquare,
    title: "AI Travel Assistant",
    description:
      "Chat with our intelligent assistant for travel advice, recommendations, and planning help.",
  },
  {
    icon: FileText,
    title: "Travel Notes",
    description:
      "Create and share beautiful travel stories with our integrated note-taking system.",
  },
  {
    icon: Sparkles,
    title: "AI-Powered Reviews",
    description:
      "Get intelligent summaries of reviews to make informed decisions quickly.",
  },
];

const stats = [
  { icon: Globe, value: "1000+", label: "Destinations" },
  { icon: Users, value: "50K+", label: "Happy Travelers" },
  { icon: Star, value: "4.9", label: "Average Rating" },
  { icon: Zap, value: "99.9%", label: "Uptime" },
];

const destinations = [
  {
    name: "Shanghai",
    country: "China",
    image:
      "https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=400&h=500&fit=crop",
    attractions: 245,
  },
  {
    name: "Beijing",
    country: "China",
    image:
      "https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=400&h=500&fit=crop",
    attractions: 312,
  },
  {
    name: "Hangzhou",
    country: "China",
    image:
      "https://images.unsplash.com/photo-1609137144813-7d9921338f24?w=400&h=500&fit=crop",
    attractions: 156,
  },
  {
    name: "Suzhou",
    country: "China",
    image:
      "https://images.unsplash.com/photo-1528164344705-47542687000d?w=400&h=500&fit=crop",
    attractions: 128,
  },
];

export default function Home() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-background relative flex items-center overflow-hidden">
        {/* Background gradient */}
        <div className="from-primary/5 to-secondary/5 via-background absolute inset-0 bg-linear-to-br" />

        {/* Background shapes */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="bg-primary/20 absolute -top-40 -right-40 h-80 w-80 rounded-full opacity-50 mix-blend-multiply blur-3xl filter" />
          <div className="bg-secondary/20 absolute -bottom-40 -left-40 h-80 w-80 rounded-full opacity-50 mix-blend-multiply blur-3xl filter" />
          <div className="bg-accent/20 absolute top-1/2 left-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full opacity-30 mix-blend-multiply blur-3xl filter" />
        </div>

        <div className="relative mx-auto w-full max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-32">
          <div className="grid items-center gap-16 lg:grid-cols-[450px_1fr]">
            {/* Left content */}
            <div className="text-center lg:text-left">
              <span className="bg-primary/10 text-primary mb-6 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium">
                <Sparkles className="h-4 w-4" />
                AI-Powered Travel Platform
              </span>
              <h1 className="text-foreground mb-6 text-4xl leading-tight font-bold sm:text-5xl lg:text-6xl">
                Your Journey Starts with
                <span className="gradient-text block">TripSphere</span>
              </h1>
              <p className="text-muted-foreground mx-auto mb-8 max-w-md text-xl lg:mx-0">
                Experience the future of travel planning with our intelligent AI
                assistant. Discover attractions, find hotels, and create
                unforgettable memories.
              </p>
              <div className="flex flex-col items-center justify-center gap-4 sm:flex-row lg:justify-start">
                <Link
                  href="/chat"
                  className="bg-primary text-primary-foreground inline-flex items-center gap-2 rounded-xl px-8 py-4 text-lg font-semibold transition-all duration-300 hover:scale-105 hover:shadow-xl"
                >
                  <MessageSquare className="h-5 w-5" />
                  Start Planning
                </Link>
                <Link
                  href="/attractions"
                  className="border-border bg-background text-foreground inline-flex items-center gap-2 rounded-xl border px-8 py-4 text-lg font-semibold shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl"
                >
                  Explore
                  <ArrowRight className="h-5 w-5" />
                </Link>
              </div>
            </div>

            {/* Right content - Placeholder for chat preview */}
            <div className="relative hidden lg:block">
              <div className="from-primary/20 to-secondary/20 absolute inset-0 rounded-3xl bg-linear-to-br blur-2xl" />
              <div className="relative">
                <ImageCarousel images={heroImages} autoPlayInterval={4000} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-muted py-20 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-16 text-center">
            <span className="bg-secondary/10 text-secondary-foreground mb-4 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium">
              <Zap className="h-4 w-4" />
              Features
            </span>
            <h2 className="text-foreground mb-4 text-3xl font-bold sm:text-4xl">
              Everything You Need for Perfect Travels
            </h2>
            <p className="text-muted-foreground mx-auto max-w-2xl text-xl">
              Our AI-powered platform provides all the tools you need to plan,
              book, and enjoy your perfect trip.
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.title}>
                  <Card className="h-full">
                    <div className="bg-primary mb-4 flex h-14 w-14 items-center justify-center rounded-2xl">
                      <Icon className="text-primary-foreground h-7 w-7" />
                    </div>
                    <h3 className="text-foreground mb-2 text-xl font-semibold">
                      {feature.title}
                    </h3>
                    <p className="text-muted-foreground">
                      {feature.description}
                    </p>
                  </Card>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Destinations Section */}
      <section className="bg-background py-20 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-12 flex items-center justify-between">
            <div>
              <span className="bg-accent/10 text-accent-foreground mb-4 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium">
                <Globe className="h-4 w-4" />
                Popular Destinations
              </span>
              <h2 className="text-foreground text-3xl font-bold sm:text-4xl">
                Explore Amazing Places
              </h2>
            </div>
            <Link
              href="/attractions"
              className="text-primary hover:text-primary/80 hidden items-center gap-2 font-medium transition-colors sm:inline-flex"
            >
              View All
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {destinations.map((destination) => (
              <div key={destination.name}>
                <Link
                  href="/attractions"
                  className="group relative block aspect-4/5 overflow-hidden rounded-2xl"
                >
                  <Image
                    src={destination.image}
                    alt={destination.name}
                    fill
                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                    className="object-cover transition-transform duration-500 group-hover:scale-110"
                    unoptimized
                  />
                  <div className="absolute inset-0 bg-linear-to-t from-black/70 via-black/20 to-transparent" />
                  <div className="absolute right-0 bottom-0 left-0 p-6 text-white">
                    <h3 className="mb-1 text-xl font-bold">
                      {destination.name}
                    </h3>
                    <p className="text-sm text-white/80">
                      {destination.country}
                    </p>
                    <p className="mt-2 text-sm text-white/60">
                      {destination.attractions} attractions
                    </p>
                  </div>
                </Link>
              </div>
            ))}
          </div>

          <div className="mt-8 text-center sm:hidden">
            <Link
              href="/attractions"
              className="text-primary inline-flex items-center gap-2 font-medium"
            >
              View All Destinations
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary text-primary-foreground py-20 lg:py-32">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <div>
            <h2 className="mb-6 text-3xl font-bold sm:text-4xl lg:text-5xl">
              Ready to Start Your Adventure?
            </h2>
          </div>
          <div>
            <p className="text-primary-foreground/80 mb-10 text-xl">
              Join thousands of travelers who use TripSphere to plan their
              perfect trips. Our AI assistant is ready to help you discover
              amazing destinations.
            </p>
          </div>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/chat"
              className="bg-background text-foreground inline-flex items-center gap-2 rounded-xl px-8 py-4 text-lg font-semibold transition-all duration-300 hover:scale-105 hover:shadow-xl"
            >
              <MessageSquare className="h-5 w-5" />
              Chat with AI Assistant
            </Link>
            <Link
              href="/register"
              className="border-primary-foreground/30 bg-primary-foreground/10 text-primary-foreground hover:bg-primary-foreground/20 inline-flex items-center gap-2 rounded-xl border px-8 py-4 text-lg font-semibold transition-all duration-300"
            >
              Create Free Account
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
