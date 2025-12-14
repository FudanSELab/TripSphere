import { Hotel } from 'lucide-react'

export default function HotelsPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-100 to-cyan-100 flex items-center justify-center">
          <Hotel className="w-12 h-12 text-blue-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Hotels</h1>
        <p className="text-xl text-gray-600 mb-8 max-w-md mx-auto">
          Hotel search and booking functionality coming soon!
        </p>
        <p className="text-gray-500">
          This page is under construction.
        </p>
      </div>
    </div>
  )
}
