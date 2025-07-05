import { Card, CardContent, CardHeader } from "@/components/ui/card";

export default function Loading() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Cover Image Skeleton */}
      <div className="h-48 bg-gradient-to-r from-purple-600/30 to-pink-600/30 relative">
        <div className="absolute inset-0 bg-black/20 animate-pulse" />
      </div>

      <div className="container mx-auto px-4 -mt-16 relative z-10">
        {/* Profile Header Skeleton */}
        <div className="flex flex-col md:flex-row items-start md:items-end space-y-4 md:space-y-0 md:space-x-6 mb-8">
          {/* Avatar Skeleton */}
          <div className="w-32 h-32 rounded-full bg-white/10 animate-pulse border-4 border-white/20" />

          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              {/* Name Skeleton */}
              <div className="h-8 w-48 bg-white/10 rounded animate-pulse" />
              {/* Badge Skeleton */}
              <div className="h-6 w-16 bg-white/10 rounded animate-pulse" />
            </div>
            {/* Description Skeleton */}
            <div className="h-6 w-64 bg-white/10 rounded animate-pulse mb-2" />
            <div className="h-5 w-full max-w-md bg-white/10 rounded animate-pulse mb-4" />
            <div className="h-4 w-32 bg-white/10 rounded animate-pulse" />
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Token Info */}
          <div className="lg:col-span-2 space-y-6">
            {/* Token Stats Card */}
            <Card className="bg-white/5 border-white/10">
              <CardHeader className="pb-3">
                <div className="h-6 w-32 bg-white/10 rounded animate-pulse" />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="space-y-2">
                      <div className="h-4 w-16 bg-white/10 rounded animate-pulse" />
                      <div className="h-6 w-20 bg-white/10 rounded animate-pulse" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Chart Card */}
            <Card className="bg-white/5 border-white/10">
              <CardHeader className="pb-3">
                <div className="h-6 w-24 bg-white/10 rounded animate-pulse" />
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-white/5 rounded animate-pulse" />
              </CardContent>
            </Card>

            {/* About Section */}
            <Card className="bg-white/5 border-white/10">
              <CardHeader className="pb-3">
                <div className="h-6 w-20 bg-white/10 rounded animate-pulse" />
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="h-4 w-full bg-white/10 rounded animate-pulse" />
                <div className="h-4 w-4/5 bg-white/10 rounded animate-pulse" />
                <div className="h-4 w-3/5 bg-white/10 rounded animate-pulse" />
              </CardContent>
            </Card>
          </div>

          {/* Right Column - Trading */}
          <div className="space-y-6">
            {/* Trading Card */}
            <Card className="bg-white/5 border-white/10">
              <CardHeader className="pb-3">
                <div className="h-6 w-20 bg-white/10 rounded animate-pulse" />
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="h-4 w-16 bg-white/10 rounded animate-pulse" />
                  <div className="h-10 bg-white/10 rounded animate-pulse" />
                </div>
                <div className="space-y-2">
                  <div className="h-4 w-20 bg-white/10 rounded animate-pulse" />
                  <div className="h-10 bg-white/10 rounded animate-pulse" />
                </div>
                <div className="h-10 bg-white/10 rounded animate-pulse" />
              </CardContent>
            </Card>

            {/* Portfolio Card */}
            <Card className="bg-white/5 border-white/10">
              <CardHeader className="pb-3">
                <div className="h-6 w-24 bg-white/10 rounded animate-pulse" />
              </CardHeader>
              <CardContent className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-white/10 animate-pulse" />
                      <div className="space-y-1">
                        <div className="h-4 w-16 bg-white/10 rounded animate-pulse" />
                        <div className="h-3 w-12 bg-white/10 rounded animate-pulse" />
                      </div>
                    </div>
                    <div className="h-4 w-16 bg-white/10 rounded animate-pulse" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
