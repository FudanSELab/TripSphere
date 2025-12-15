'use client'

import Link from "next/link";
import Image from "next/image";
import { MapPin, Hotel, Calendar, MessageSquare, FileText, Sparkles, ArrowRight, Star, Users, Globe, Zap } from "lucide-react";
import { Card } from "@/components/ui/card";
import { AnimateInView, StaggerContainer, StaggerItem } from "@/components/ui/animate-container";
import { ChatWindow } from "@/components/chat/chat-window";

const features = [
  {
    icon: MapPin,
    title: 'Discover Attractions',
    description: 'Explore thousands of attractions with AI-powered recommendations tailored to your interests.',
    color: 'from-rose-500 to-orange-500',
  },
  {
    icon: Hotel,
    title: 'Find Perfect Hotels',
    description: 'Get personalized hotel recommendations based on your preferences, budget, and travel style.',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: Calendar,
    title: 'Smart Itinerary Planning',
    description: 'Let our AI create optimized travel itineraries with intelligent route planning.',
    color: 'from-green-500 to-emerald-500',
  },
  {
    icon: MessageSquare,
    title: 'AI Travel Assistant',
    description: 'Chat with our intelligent assistant for travel advice, recommendations, and planning help.',
    color: 'from-purple-500 to-pink-500',
  },
  {
    icon: FileText,
    title: 'Travel Notes',
    description: 'Create and share beautiful travel stories with our integrated note-taking system.',
    color: 'from-amber-500 to-yellow-500',
  },
  {
    icon: Sparkles,
    title: 'AI-Powered Reviews',
    description: 'Get intelligent summaries of reviews to make informed decisions quickly.',
    color: 'from-indigo-500 to-violet-500',
  },
];

const stats = [
  { icon: Globe, value: '1000+', label: 'Destinations' },
  { icon: Users, value: '50K+', label: 'Happy Travelers' },
  { icon: Star, value: '4.9', label: 'Average Rating' },
  { icon: Zap, value: '99.9%', label: 'Uptime' },
];

const destinations = [
  { 
    name: 'Shanghai', 
    country: 'China',
    image: 'https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=400&h=500&fit=crop',
    attractions: 245,
  },
  { 
    name: 'Beijing', 
    country: 'China',
    image: 'https://images.unsplash.com/photo-1508804185872-d7badad00f7d?w=400&h=500&fit=crop',
    attractions: 312,
  },
  { 
    name: 'Hangzhou', 
    country: 'China',
    image: 'https://images.unsplash.com/photo-1591122947157-26bad3a117d2?w=400&h=500&fit=crop',
    attractions: 156,
  },
  { 
    name: 'Suzhou', 
    country: 'China',
    image: 'https://images.unsplash.com/photo-1528164344705-47542687000d?w=400&h=500&fit=crop',
    attractions: 128,
  },
];

export default function Home() {
  return (
    <div>
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center overflow-hidden bg-white">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-white to-secondary-50" />
        
        {/* Animated background shapes */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-float" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary-200 rounded-full mix-blend-multiply filter blur-3xl opacity-50 animate-float" style={{ animationDelay: '-1.5s' }} />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-accent-200 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-float" style={{ animationDelay: '-3s' }} />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32 w-full">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left content */}
            <AnimateInView className="text-center lg:text-left">
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100 text-primary-700 rounded-full text-sm font-medium mb-6">
                <Sparkles className="w-4 h-4" />
                AI-Powered Travel Platform
              </span>
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight mb-6">
                Your Journey Starts with
                <span className="gradient-text block">TripSphere</span>
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-xl mx-auto lg:mx-0">
                Experience the future of travel planning with our intelligent AI assistant. Discover attractions, find hotels, and create unforgettable memories.
              </p>
              <div className="flex flex-col sm:flex-row items-center gap-4 justify-center lg:justify-start">
                <Link
                  href="/chat"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-primary-600 to-secondary-600 text-white rounded-xl text-lg font-semibold hover:shadow-xl hover:scale-105 transition-all duration-300"
                >
                  <MessageSquare className="w-5 h-5" />
                  Start Planning
                </Link>
                <Link
                  href="/attractions"
                  className="inline-flex items-center gap-2 px-8 py-4 bg-white text-gray-700 rounded-xl text-lg font-semibold shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300 border border-gray-200"
                >
                  Explore
                  <ArrowRight className="w-5 h-5" />
                </Link>
              </div>
            </AnimateInView>

            {/* Right content - Placeholder for chat preview */}
            <AnimateInView delay={0.2} className="relative hidden lg:block">
              <div className="absolute inset-0 bg-gradient-to-br from-primary-500/20 to-secondary-500/20 rounded-3xl blur-2xl" />
              <div className="relative">
                <ChatWindow />
              </div>
            </AnimateInView>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-white border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <StaggerContainer className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => {
              const Icon = stat.icon;
              return (
                <StaggerItem
                  key={stat.label}
                  className="text-center"
                >
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-primary-100 text-primary-600 rounded-xl mb-3">
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="text-3xl font-bold text-gray-900">{stat.value}</div>
                  <div className="text-gray-500">{stat.label}</div>
                </StaggerItem>
              );
            })}
          </StaggerContainer>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 lg:py-32 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <AnimateInView className="text-center mb-16">
            <span className="inline-flex items-center gap-2 px-4 py-2 bg-secondary-100 text-secondary-700 rounded-full text-sm font-medium mb-4">
              <Zap className="w-4 h-4" />
              Features
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need for Perfect Travels
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our AI-powered platform provides all the tools you need to plan, book, and enjoy your perfect trip.
            </p>
          </AnimateInView>

          <StaggerContainer className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <StaggerItem key={feature.title}>
                  <Card hover>
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4`}>
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-gray-600">
                    {feature.description}
                  </p>
                  </Card>
                </StaggerItem>
              );
            })}
          </StaggerContainer>
        </div>
      </section>

      {/* Destinations Section */}
      <section className="py-20 lg:py-32 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-12">
            <AnimateInView>
              <span className="inline-flex items-center gap-2 px-4 py-2 bg-accent-100 text-accent-700 rounded-full text-sm font-medium mb-4">
                <Globe className="w-4 h-4" />
                Popular Destinations
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900">
                Explore Amazing Places
              </h2>
            </AnimateInView>
            <Link
              href="/attractions"
              className="hidden sm:inline-flex items-center gap-2 text-primary-600 font-medium hover:text-primary-700 transition-colors"
            >
              View All
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <StaggerContainer className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {destinations.map((destination) => (
              <StaggerItem key={destination.name}>
                <Link
                  href="/attractions"
                  className="group relative rounded-2xl overflow-hidden aspect-[4/5] block"
                >
                <Image
                  src={destination.image}
                  alt={destination.name}
                  fill
                  className="object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-6 text-white">
                  <h3 className="text-xl font-bold mb-1">{destination.name}</h3>
                  <p className="text-white/80 text-sm">{destination.country}</p>
                  <p className="text-white/60 text-sm mt-2">
                    {destination.attractions} attractions
                  </p>
                </div>
                </Link>
              </StaggerItem>
            ))}
          </StaggerContainer>

          <div className="sm:hidden mt-8 text-center">
            <Link
              href="/attractions"
              className="inline-flex items-center gap-2 text-primary-600 font-medium"
            >
              View All Destinations
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 lg:py-32 bg-gradient-to-br from-primary-600 to-secondary-600 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <AnimateInView>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
              Ready to Start Your Adventure?
            </h2>
          </AnimateInView>
          <AnimateInView delay={0.1}>
            <p className="text-xl text-white/80 mb-10">
              Join thousands of travelers who use TripSphere to plan their perfect trips. Our AI assistant is ready to help you discover amazing destinations.
            </p>
          </AnimateInView>
          <AnimateInView delay={0.2} className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-primary-600 rounded-xl text-lg font-semibold hover:shadow-xl hover:scale-105 transition-all duration-300"
            >
              <MessageSquare className="w-5 h-5" />
              Chat with AI Assistant
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white/10 text-white rounded-xl text-lg font-semibold hover:bg-white/20 transition-all duration-300 border border-white/30"
            >
              Create Free Account
            </Link>
          </AnimateInView>
        </div>
      </section>
    </div>
  );
}
