"use client";

import {
  AnimateInView,
  StaggerContainer,
  StaggerItem,
} from "@/components/ui/animate-container";
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
    color: "from-rose-500 to-orange-500",
  },
  {
    icon: Hotel,
    title: "Find Perfect Hotels",
    description:
      "Get personalized hotel recommendations based on your preferences, budget, and travel style.",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: Calendar,
    title: "Smart Itinerary Planning",
    description:
      "Let our AI create optimized travel itineraries with intelligent route planning.",
    color: "from-green-500 to-emerald-500",
  },
  {
    icon: MessageSquare,
    title: "AI Travel Assistant",
    description:
      "Chat with our intelligent assistant for travel advice, recommendations, and planning help.",
    color: "from-purple-500 to-pink-500",
  },
  {
    icon: FileText,
    title: "Travel Notes",
    description:
      "Create and share beautiful travel stories with our integrated note-taking system.",
    color: "from-amber-500 to-yellow-500",
  },
  {
    icon: Sparkles,
    title: "AI-Powered Reviews",
    description:
      "Get intelligent summaries of reviews to make informed decisions quickly.",
    color: "from-indigo-500 to-violet-500",
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
      <section className="relative flex min-h-[90vh] items-center overflow-hidden bg-white">
        {/* Background gradient */}
        <div className="from-primary-50 to-secondary-50 absolute inset-0 bg-gradient-to-br via-white" />

        {/* Animated background shapes */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="bg-primary-200 animate-float absolute -top-40 -right-40 h-80 w-80 rounded-full opacity-50 mix-blend-multiply blur-3xl filter" />
          <div
            className="bg-secondary-200 animate-float absolute -bottom-40 -left-40 h-80 w-80 rounded-full opacity-50 mix-blend-multiply blur-3xl filter"
            style={{ animationDelay: "-1.5s" }}
          />
          <div
            className="bg-accent-200 animate-float absolute top-1/2 left-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 rounded-full opacity-30 mix-blend-multiply blur-3xl filter"
            style={{ animationDelay: "-3s" }}
          />
        </div>

        <div className="relative mx-auto w-full max-w-7xl px-4 py-20 sm:px-6 lg:px-8 lg:py-32">
          <div className="grid items-center gap-16 lg:grid-cols-[450px_1fr]">
            {/* Left content */}
            <AnimateInView className="text-center lg:text-left">
              <span className="bg-primary-100 text-primary-700 mb-6 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium">
                <Sparkles className="h-4 w-4" />
                AI-Powered Travel Platform
              </span>
              <h1 className="mb-6 text-4xl leading-tight font-bold text-gray-900 sm:text-5xl lg:text-6xl">
                Your Journey Starts with
                <span className="gradient-text block">TripSphere</span>
              </h1>
              <p className="mx-auto mb-8 max-w-md text-xl text-gray-600 lg:mx-0">
                Experience the future of travel planning with our intelligent AI
                assistant. Discover attractions, find hotels, and create
                unforgettable memories.
              </p>
              <div className="flex flex-col items-center justify-center gap-4 sm:flex-row lg:justify-start">
                <Link
                  href="/chat"
                  className="from-primary-600 to-secondary-600 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r px-8 py-4 text-lg font-semibold text-white transition-all duration-300 hover:scale-105 hover:shadow-xl"
                >
                  <MessageSquare className="h-5 w-5" />
                  Start Planning
                </Link>
                <Link
                  href="/attractions"
                  className="inline-flex items-center gap-2 rounded-xl border border-gray-200 bg-white px-8 py-4 text-lg font-semibold text-gray-700 shadow-lg transition-all duration-300 hover:scale-105 hover:shadow-xl"
                >
                  Explore
                  <ArrowRight className="h-5 w-5" />
                </Link>
              </div>
            </AnimateInView>

            {/* Right content - Placeholder for chat preview */}
            <AnimateInView delay={0.2} className="relative hidden lg:block">
              <div className="from-primary-500/20 to-secondary-500/20 absolute inset-0 rounded-3xl bg-gradient-to-br blur-2xl" />
              <div className="relative">
                <ImageCarousel images={heroImages} autoPlayInterval={4000} />
              </div>
            </AnimateInView>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="border-y border-gray-100 bg-white py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <StaggerContainer className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <StaggerItem key={stat.label} className="text-center">
                  <div className="bg-primary-100 text-primary-600 mb-3 inline-flex h-12 w-12 items-center justify-center rounded-xl">
                    <Icon className="h-6 w-6" />
                  </div>
                  <div className="text-3xl font-bold text-gray-900">
                    {stat.value}
                  </div>
                  <div className="text-gray-500">{stat.label}</div>
                </StaggerItem>
              );
            })}
          </StaggerContainer>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-gray-50 py-20 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <AnimateInView className="mb-16 text-center">
            <span className="bg-secondary-100 text-secondary-700 mb-4 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium">
              <Zap className="h-4 w-4" />
              Features
            </span>
            <h2 className="mb-4 text-3xl font-bold text-gray-900 sm:text-4xl">
              Everything You Need for Perfect Travels
            </h2>
            <p className="mx-auto max-w-2xl text-xl text-gray-600">
              Our AI-powered platform provides all the tools you need to plan,
              book, and enjoy your perfect trip.
            </p>
          </AnimateInView>

          <StaggerContainer className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <StaggerItem key={feature.title}>
                  <Card hover className="h-full">
                    <div
                      className={`h-14 w-14 rounded-2xl bg-gradient-to-br ${feature.color} mb-4 flex items-center justify-center`}
                    >
                      <Icon className="h-7 w-7 text-white" />
                    </div>
                    <h3 className="mb-2 text-xl font-semibold text-gray-900">
                      {feature.title}
                    </h3>
                    <p className="text-gray-600">{feature.description}</p>
                  </Card>
                </StaggerItem>
              );
            })}
          </StaggerContainer>
        </div>
      </section>

      {/* Destinations Section */}
      <section className="bg-white py-20 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="mb-12 flex items-center justify-between">
            <AnimateInView>
              <span className="bg-accent-100 text-accent-700 mb-4 inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium">
                <Globe className="h-4 w-4" />
                Popular Destinations
              </span>
              <h2 className="text-3xl font-bold text-gray-900 sm:text-4xl">
                Explore Amazing Places
              </h2>
            </AnimateInView>
            <Link
              href="/attractions"
              className="text-primary-600 hover:text-primary-700 hidden items-center gap-2 font-medium transition-colors sm:inline-flex"
            >
              View All
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          <StaggerContainer className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {destinations.map((destination) => (
              <StaggerItem key={destination.name}>
                <Link
                  href="/attractions"
                  className="group relative block aspect-[4/5] overflow-hidden rounded-2xl"
                >
                  <Image
                    src={destination.image}
                    alt={destination.name}
                    fill
                    sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
                    className="object-cover transition-transform duration-500 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
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
              </StaggerItem>
            ))}
          </StaggerContainer>

          <div className="mt-8 text-center sm:hidden">
            <Link
              href="/attractions"
              className="text-primary-600 inline-flex items-center gap-2 font-medium"
            >
              View All Destinations
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="from-primary-600 to-secondary-600 bg-gradient-to-br py-20 text-white lg:py-32">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <AnimateInView>
            <h2 className="mb-6 text-3xl font-bold sm:text-4xl lg:text-5xl">
              Ready to Start Your Adventure?
            </h2>
          </AnimateInView>
          <AnimateInView delay={0.1}>
            <p className="mb-10 text-xl text-white/80">
              Join thousands of travelers who use TripSphere to plan their
              perfect trips. Our AI assistant is ready to help you discover
              amazing destinations.
            </p>
          </AnimateInView>
          <AnimateInView
            delay={0.2}
            className="flex flex-col items-center justify-center gap-4 sm:flex-row"
          >
            <Link
              href="/chat"
              className="text-primary-600 inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-lg font-semibold transition-all duration-300 hover:scale-105 hover:shadow-xl"
            >
              <MessageSquare className="h-5 w-5" />
              Chat with AI Assistant
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 rounded-xl border border-white/30 bg-white/10 px-8 py-4 text-lg font-semibold text-white transition-all duration-300 hover:bg-white/20"
            >
              Create Free Account
            </Link>
          </AnimateInView>
        </div>
      </section>
    </div>
  );
}
