import { MessageSquare } from 'lucide-react'

export default function ChatPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-purple-100 to-pink-100 flex items-center justify-center">
          <MessageSquare className="w-12 h-12 text-purple-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">AI Travel Assistant</h1>
        <p className="text-xl text-gray-600 mb-8 max-w-md mx-auto">
          Chat with our AI assistant coming soon!
        </p>
        <p className="text-gray-500">
          This page is under construction.
        </p>
      </div>
    </div>
  )
}
