import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ArrowRight, Users, TrendingUp, Zap, Shield } from "lucide-react"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Navigation */}
      <nav className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500" />
              <span className="text-xl font-bold text-white">BuildersFund</span>
            </div>
            <div className="flex items-center space-x-6">
              <Link href="/fund" className="text-white/80 hover:text-white transition-colors">
                Fund
              </Link>
              <Link href="/builder" className="text-white/80 hover:text-white transition-colors">
                Launch Token
              </Link>
              <Button variant="outline" className="border-white/20 text-white hover:bg-white/10 bg-transparent">
                Connect Wallet
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-7xl font-bold text-white mb-6">
            The Future of
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              {" "}
              Builder Economy
            </span>
          </h1>
          <p className="text-xl text-white/80 mb-8 leading-relaxed">
            A permissionless index fund that invests in the most promising builders in Web3. Powered by AI agents,
            backed by community, built for the future.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/fund">
              <Button
                size="lg"
                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-3"
              >
                Invest in Fund
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/builder">
              <Button
                size="lg"
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10 px-8 py-3 bg-transparent"
              >
                Launch Your Token
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader>
              <Users className="h-8 w-8 text-purple-400 mb-2" />
              <CardTitle className="text-white">Permissionless</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-white/70">
                Anyone can join the builder economy by launching their personal token with minimum liquidity.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader>
              <Zap className="h-8 w-8 text-yellow-400 mb-2" />
              <CardTitle className="text-white">AI-Powered</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-white/70">
                Advanced AI agents analyze and select the most promising builder tokens for the fund.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader>
              <TrendingUp className="h-8 w-8 text-green-400 mb-2" />
              <CardTitle className="text-white">Diversified</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-white/70">
                Spread risk across multiple builder tokens while supporting the Web3 ecosystem.
              </CardDescription>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardHeader>
              <Shield className="h-8 w-8 text-blue-400 mb-2" />
              <CardTitle className="text-white">Transparent</CardTitle>
            </CardHeader>
            <CardContent>
              <CardDescription className="text-white/70">
                All fund decisions and holdings are transparent and verifiable on-chain.
              </CardDescription>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">How It Works</h2>
          <p className="text-white/80 text-lg">Simple steps to participate in the builder economy</p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-xl">1</span>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Builders Launch Tokens</h3>
            <p className="text-white/70">
              Builders create their personal tokens with minimum liquidity requirements to join the ecosystem.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-xl">2</span>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">AI Agent Selects</h3>
            <p className="text-white/70">
              Our AI fund manager analyzes and selects the most promising builder tokens for investment.
            </p>
          </div>

          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-xl">3</span>
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Investors Participate</h3>
            <p className="text-white/70">
              Buy fund tokens to gain exposure to a diversified portfolio of builder tokens.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <Card className="bg-gradient-to-r from-purple-600/20 to-pink-600/20 border-white/10 backdrop-blur-sm">
          <CardContent className="text-center py-16">
            <h2 className="text-3xl font-bold text-white mb-4">Ready to Join the Builder Economy?</h2>
            <p className="text-white/80 mb-8 text-lg">Start investing in the future of Web3 builders today.</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/fund">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-3"
                >
                  View Fund Details
                </Button>
              </Link>
              <Link href="/builder">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-white/20 text-white hover:bg-white/10 px-8 py-3 bg-transparent"
                >
                  Launch Your Token
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-white/60">
            <p>&copy; 2024 BuildersFund. Building the future of decentralized finance.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
