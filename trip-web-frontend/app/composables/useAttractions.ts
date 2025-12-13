import type { Attraction } from '~/types'

export const useAttractions = () => {
  const runtimeConfig = useRuntimeConfig()
  const attractionServiceUrl = runtimeConfig.public.attractionServiceUrl

  const fetchAttraction = async (id: string): Promise<Attraction | null> => {
    try {
      // In production, this would call the actual API
      // const response = await fetch(`${attractionServiceUrl}/attractions/${id}`)
      // const data = await response.json()
      // return data

      // For now, return mock data based on ID
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // Mock data - in production this would come from the API
      const mockAttractions: Record<string, Attraction> = {
        '1': {
          id: '1',
          name: 'The Bund',
          description: 'The Bund is a waterfront area in central Shanghai, featuring a mix of historical colonial-era buildings and modern skyscrapers. It offers stunning views of the Huangpu River and the futuristic Pudong skyline across the water. A must-visit destination for any traveler to Shanghai, the Bund combines history, architecture, and vibrant city life.',
          address: { 
            country: 'China', 
            province: 'Shanghai', 
            city: 'Shanghai', 
            county: 'Huangpu', 
            district: '', 
            street: 'Zhongshan East 1st Road' 
          },
          location: { lng: 121.4883, lat: 31.2319 },
          category: 'Landmark',
          rating: 4.8,
          openingHours: '24 hours',
          ticketPrice: 'Free',
          images: [
            'https://images.unsplash.com/photo-1474181487882-5abf3f0ba6c2?w=1200&h=800&fit=crop',
            'https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=1200&h=800&fit=crop',
            'https://images.unsplash.com/photo-1538428494232-9c0d8a3ab403?w=1200&h=800&fit=crop',
          ],
          tags: ['Historic', 'Scenic', 'Night View', 'Photography'],
        },
        '2': {
          id: '2',
          name: 'Yu Garden',
          description: 'A classical Chinese garden located in the Old City of Shanghai, featuring traditional architecture and landscapes.',
          address: { country: 'China', province: 'Shanghai', city: 'Shanghai', county: 'Huangpu', district: '', street: 'Anren Street' },
          location: { lng: 121.4920, lat: 31.2270 },
          category: 'Garden',
          rating: 4.6,
          openingHours: '8:30 AM - 5:00 PM',
          ticketPrice: '¥40',
          images: ['https://images.unsplash.com/photo-1548919973-5cef591cdbc9?w=600&h=400&fit=crop'],
          tags: ['Traditional', 'Cultural', 'Architecture'],
        },
      }

      return mockAttractions[id] || null
    } catch (error) {
      console.error('Error fetching attraction:', error)
      throw error
    }
  }

  const fetchAttractions = async (): Promise<Attraction[]> => {
    try {
      // In production, this would call the actual API
      // const response = await fetch(`${attractionServiceUrl}/attractions`)
      // const data = await response.json()
      // return data

      await new Promise(resolve => setTimeout(resolve, 300))
      
      // Mock data - returning the list from the index page
      return []
    } catch (error) {
      console.error('Error fetching attractions:', error)
      throw error
    }
  }

  return {
    fetchAttraction,
    fetchAttractions,
  }
}
