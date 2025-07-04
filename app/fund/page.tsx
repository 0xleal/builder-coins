"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { ArrowLeft, TrendingUp, Users, DollarSign, Activity, ExternalLink } from "lucide-react"

// Mock data
const fundMetrics = {
  totalValue: "$2,450,000",
  tokenPrice: "$24.50",
  totalSupply: "100,000 BF",
  holders: "1,247",
  performance24h: "+5.2%",
  performance7d: "+12.8%",
  performance30d: "+34.5%",
  aum: "$2.45M",
}

const builders = [
  {
    id: 1,
    name: "Alex Chen",
    ticker: "ALEX",
    avatar: "/placeholder.svg?height=40&width=40",
    allocation: "8.5%",
    tokenPrice: "$12.34",
    change24h: "+3.2%",
    marketCap: "$123,400",
    description: "Full-stack developer building DeFi protocols",
    projects: ["DeFiSwap", "YieldFarm Pro"],
    followers: "2.1K",
  },
  {
    id: 2,
    name: "Sarah Kim",
    ticker: "SARAH",
    avatar: "/placeholder.svg?height=40&width=40",
    allocation: "7.2%",
    tokenPrice: "$8.76",
    change24h: "-1.5%",
    marketCap: "$87,600",
    description: "Smart contract auditor and security researcher",
    projects: ["SecureAudit", "ChainGuard"],
    followers: "1.8K",
  },
  {
    id: 3,
    name: "Marcus Johnson",
    ticker: "MARC",
    avatar: "/placeholder.svg?height=40&width=40",
    allocation: "6.8%",
    tokenPrice: "$15.23",
    change24h: "+7.1%",
    marketCap: "$152,300",
    description: "NFT marketplace creator and digital artist",
    projects: ["ArtChain", "NFTLaunch"],
    followers: "3.5K",
  },
  {
    id: 4,
    name: "Emily Rodriguez",
    ticker: "EMILY",
    avatar: "/placeholder.svg?height=40&width=40",
    allocation: "5.9%",
    tokenPrice: "$9.87",
    change24h: "+2.8%",
    marketCap: "$98,700",
    description: "Layer 2 scaling solutions architect",
    projects: ["FastChain", "ScaleUp"],
    followers: "1.2K",
  },
]

export default function FundPage() {
  const [buyAmount, setBuyAmount] = useState("")
  const [sellAmount, setSellAmount] = useState("")
  const [selectedBuilder, setSelectedBuilder] = useState(null)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/" className="flex items-center space-x-2 text-white/80 hover:text-white">
                <ArrowLeft className="h-4 w-4" />
                <span>Back</span>
              </Link>
              <div className="flex items-center space-x-2">
                <div className="h-8 w-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500" />
                <span className="text-xl font-bold text-white">BuildersFund</span>
              </div>
            </div>
            <Button variant="outline" className="border-white/20 text-white hover:bg-white/10 bg-transparent">
              Connect Wallet
            </Button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-8">
        {/* Fund Overview */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">BuildersFund Index</h1>
          <p className="text-white/80 text-lg">Diversified exposure to the most promising Web3 builders</p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Total Value</p>
                  <p className="text-white text-xl font-bold">{fundMetrics.totalValue}</p>
                </div>
                <DollarSign className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Token Price</p>
                  <p className="text-white text-xl font-bold">{fundMetrics.tokenPrice}</p>
                </div>
                <Activity className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">24h Change</p>
                  <p className="text-green-400 text-xl font-bold">{fundMetrics.performance24h}</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Holders</p>
                  <p className="text-white text-xl font-bold">{fundMetrics.holders}</p>
                </div>
                <Users className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Trading Interface */}
          <div className="lg:col-span-1">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">Trade Fund Token</CardTitle>
                <CardDescription className="text-white/70">Buy or sell BuildersFund tokens</CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="buy" className="w-full">
                  <TabsList className="grid w-full grid-cols-2 bg-white/10">
                    <TabsTrigger value="buy" className="text-white data-[state=active]:bg-green-600">
                      Buy
                    </TabsTrigger>
                    <TabsTrigger value="sell" className="text-white data-[state=active]:bg-red-600">
                      Sell
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="buy" className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="buy-amount" className="text-white">
                        Amount (ETH)
                      </Label>
                      <Input
                        id="buy-amount"
                        placeholder="0.0"
                        value={buyAmount}
                        onChange={(e) => setBuyAmount(e.target.value)}
                        className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                      />
                      <p className="text-white/60 text-sm">
                        ≈ {buyAmount ? ((Number.parseFloat(buyAmount) / 24.5) * 1000).toFixed(2) : "0"} BF tokens
                      </p>
                    </div>
                    <Button className="w-full bg-green-600 hover:bg-green-700 text-white">Buy Fund Tokens</Button>
                  </TabsContent>

                  <TabsContent value="sell" className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="sell-amount" className="text-white">
                        Amount (BF)
                      </Label>
                      <Input
                        id="sell-amount"
                        placeholder="0.0"
                        value={sellAmount}
                        onChange={(e) => setSellAmount(e.target.value)}
                        className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                      />
                      <p className="text-white/60 text-sm">
                        ≈ {sellAmount ? ((Number.parseFloat(sellAmount) * 24.5) / 1000).toFixed(4) : "0"} ETH
                      </p>
                    </div>
                    <Button className="w-full bg-red-600 hover:bg-red-700 text-white">Sell Fund Tokens</Button>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>

            {/* Performance Card */}
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm mt-6">
              <CardHeader>
                <CardTitle className="text-white">Performance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-white/70">24h</span>
                  <span className="text-green-400 font-semibold">{fundMetrics.performance24h}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">7d</span>
                  <span className="text-green-400 font-semibold">{fundMetrics.performance7d}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">30d</span>
                  <span className="text-green-400 font-semibold">{fundMetrics.performance30d}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Builders Portfolio */}
          <div className="lg:col-span-2">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">Fund Holdings</CardTitle>
                <CardDescription className="text-white/70">Builders currently invested by the fund</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {builders.map((builder) => (
                    <Dialog key={builder.id}>
                      <DialogTrigger asChild>
                        <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors">
                          <div className="flex items-center space-x-4">
                            <Avatar>
                              <AvatarImage src={builder.avatar || "/placeholder.svg"} alt={builder.name} />
                              <AvatarFallback className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                                {builder.name
                                  .split(" ")
                                  .map((n) => n[0])
                                  .join("")}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <div className="flex items-center space-x-2">
                                <h3 className="text-white font-semibold">{builder.name}</h3>
                                <Badge variant="secondary" className="bg-white/10 text-white/80">
                                  ${builder.ticker}
                                </Badge>
                              </div>
                              <p className="text-white/60 text-sm">{builder.description}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-white font-semibold">{builder.allocation}</p>
                            <p
                              className={`text-sm ${builder.change24h.startsWith("+") ? "text-green-400" : "text-red-400"}`}
                            >
                              {builder.change24h}
                            </p>
                          </div>
                        </div>
                      </DialogTrigger>

                      <DialogContent className="bg-slate-900 border-white/10 text-white">
                        <DialogHeader>
                          <DialogTitle className="flex items-center space-x-3">
                            <Avatar>
                              <AvatarImage src={builder.avatar || "/placeholder.svg"} alt={builder.name} />
                              <AvatarFallback className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                                {builder.name
                                  .split(" ")
                                  .map((n) => n[0])
                                  .join("")}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <h3 className="text-xl">{builder.name}</h3>
                              <Badge variant="secondary" className="bg-white/10 text-white/80">
                                ${builder.ticker}
                              </Badge>
                            </div>
                          </DialogTitle>
                          <DialogDescription className="text-white/70">{builder.description}</DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-white/60 text-sm">Token Price</p>
                              <p className="text-white text-lg font-semibold">{builder.tokenPrice}</p>
                            </div>
                            <div>
                              <p className="text-white/60 text-sm">24h Change</p>
                              <p
                                className={`text-lg font-semibold ${builder.change24h.startsWith("+") ? "text-green-400" : "text-red-400"}`}
                              >
                                {builder.change24h}
                              </p>
                            </div>
                            <div>
                              <p className="text-white/60 text-sm">Market Cap</p>
                              <p className="text-white text-lg font-semibold">{builder.marketCap}</p>
                            </div>
                            <div>
                              <p className="text-white/60 text-sm">Followers</p>
                              <p className="text-white text-lg font-semibold">{builder.followers}</p>
                            </div>
                          </div>

                          <div>
                            <p className="text-white/60 text-sm mb-2">Projects</p>
                            <div className="flex flex-wrap gap-2">
                              {builder.projects.map((project, index) => (
                                <Badge key={index} variant="outline" className="border-white/20 text-white/80">
                                  {project}
                                </Badge>
                              ))}
                            </div>
                          </div>

                          <Button className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
                            View Builder Profile
                            <ExternalLink className="ml-2 h-4 w-4" />
                          </Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
