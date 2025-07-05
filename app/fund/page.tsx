"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { TrendingUp, Users, DollarSign, ExternalLink } from "lucide-react";
import { FUND_MANAGER_ADDRESS, TALENT_TOKEN } from "@/lib/constants";
import { usePrivy, useWallets } from "@privy-io/react-auth";
import { useAccount, useReadContract, useWriteContract } from "wagmi";
import {
  createPublicClient,
  http,
  erc20Abi,
  parseEther,
  formatUnits,
} from "viem";
import { base } from "viem/chains";
import { FundManagerPortfolio } from "@/lib/types";

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
];

export default function FundPage() {
  const [depositAmount, setDepositAmount] = useState("");
  const { ready, authenticated } = usePrivy();
  const account = useAccount();
  const wallets = useWallets();
  const { writeContractAsync } = useWriteContract();
  const { data: balance } = useReadContract({
    abi: erc20Abi,
    chainId: base.id,
    address: TALENT_TOKEN.address as `0x${string}`,
    functionName: "balanceOf",
    args: [account.address as `0x${string}`],
  });
  const [fundManagerPortfolio, setFundManagerPortfolio] =
    useState<FundManagerPortfolio | null>(null);

  useEffect(() => {
    const fetchFundManagerPortfolio = async () => {
      const response = await fetch("/api/fund-manager-portfolio");
      const data = await response.json();
      setFundManagerPortfolio(data);
    };

    fetchFundManagerPortfolio();
  }, []);

  const client = createPublicClient({ chain: base, transport: http() });

  const depositLiquidity = async () => {
    if (!ready || !authenticated || !account) return;

    if (balance && parseEther(depositAmount) > balance) {
      console.log("Insufficient balance");
      return;
    }

    const wallet = wallets.wallets.find(
      (w) => w.address.toLowerCase() === account.address?.toLowerCase()
    );

    if (!wallet) {
      console.log("Wallet not found");
      return;
    }

    await wallet.switchChain(base.id);

    const tx = await writeContractAsync({
      address: TALENT_TOKEN.address as `0x${string}`,
      abi: erc20Abi,
      chainId: base.id,
      functionName: "transfer",
      args: [FUND_MANAGER_ADDRESS, parseEther(depositAmount)],
      account: account.address as `0x${string}`,
    });

    await client.waitForTransactionReceipt({
      hash: tx,
    });

    setDepositAmount("");
  };

  return (
    <>
      <div className="container mx-auto px-4 py-8">
        {/* Fund Overview */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Builders Fund Index
          </h1>
          <p className="text-white/80 text-lg">
            Diversified exposure to the most promising Web3 builders
          </p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-8">
          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Total Value</p>
                  <p className="text-white text-xl font-bold">
                    ${fundManagerPortfolio?.value || 0}
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Liquidity Available</p>
                  <p className="text-white text-xl font-bold">
                    ${fundManagerPortfolio?.liquidity_available || 0}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-white/60 text-sm">Builder Coins Held</p>
                  <p className="text-green-400 text-xl font-bold">
                    {fundManagerPortfolio?.builder_coins_held || 0}
                  </p>
                </div>
                <Users className="h-8 w-8 text-green-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Trading Interface */}
          <div className="lg:col-span-1">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">Provide Liquidity</CardTitle>
                <CardDescription className="text-white/70">
                  Provide liquidity to the fund. Fees and rewards will be
                  distributed over time to liquidity providers
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <Label htmlFor="buy-amount" className="text-white">
                    Deposit
                  </Label>
                  <p className="text-white/60 text-sm">
                    $TALENT: {balance ? formatUnits(balance, 18) : "0"}
                  </p>
                  <Input
                    id="buy-amount"
                    placeholder="0.0"
                    value={depositAmount}
                    onChange={(e) => setDepositAmount(e.target.value)}
                    className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                  />
                </div>
                <Button
                  className="w-full bg-green-600 hover:bg-green-700 text-white mt-3"
                  onClick={depositLiquidity}
                  disabled={
                    !ready ||
                    !authenticated ||
                    !account ||
                    !balance ||
                    !depositAmount
                  }
                >
                  Provide Liquidity
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Builders Portfolio */}
          <div className="lg:col-span-2">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white">Fund Holdings</CardTitle>
                <CardDescription className="text-white/70">
                  Builders currently invested by the fund
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {builders.map((builder) => (
                    <Dialog key={builder.id}>
                      <DialogTrigger asChild>
                        <div className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 cursor-pointer transition-colors">
                          <div className="flex items-center space-x-4">
                            <Avatar>
                              <AvatarImage
                                src={builder.avatar || "/placeholder.svg"}
                                alt={builder.name}
                              />
                              <AvatarFallback className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                                {builder.name
                                  .split(" ")
                                  .map((n) => n[0])
                                  .join("")}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <div className="flex items-center space-x-2">
                                <h3 className="text-white font-semibold">
                                  {builder.name}
                                </h3>
                                <Badge
                                  variant="secondary"
                                  className="bg-white/10 text-white/80"
                                >
                                  ${builder.ticker}
                                </Badge>
                              </div>
                              <p className="text-white/60 text-sm">
                                {builder.description}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-white font-semibold">
                              {builder.allocation}
                            </p>
                            <p
                              className={`text-sm ${
                                builder.change24h.startsWith("+")
                                  ? "text-green-400"
                                  : "text-red-400"
                              }`}
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
                              <AvatarImage
                                src={builder.avatar || "/placeholder.svg"}
                                alt={builder.name}
                              />
                              <AvatarFallback className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                                {builder.name
                                  .split(" ")
                                  .map((n) => n[0])
                                  .join("")}
                              </AvatarFallback>
                            </Avatar>
                            <div>
                              <h3 className="text-xl">{builder.name}</h3>
                              <Badge
                                variant="secondary"
                                className="bg-white/10 text-white/80"
                              >
                                ${builder.ticker}
                              </Badge>
                            </div>
                          </DialogTitle>
                          <DialogDescription className="text-white/70">
                            {builder.description}
                          </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-white/60 text-sm">
                                Token Price
                              </p>
                              <p className="text-white text-lg font-semibold">
                                {builder.tokenPrice}
                              </p>
                            </div>
                            <div>
                              <p className="text-white/60 text-sm">
                                24h Change
                              </p>
                              <p
                                className={`text-lg font-semibold ${
                                  builder.change24h.startsWith("+")
                                    ? "text-green-400"
                                    : "text-red-400"
                                }`}
                              >
                                {builder.change24h}
                              </p>
                            </div>
                            <div>
                              <p className="text-white/60 text-sm">
                                Market Cap
                              </p>
                              <p className="text-white text-lg font-semibold">
                                {builder.marketCap}
                              </p>
                            </div>
                            <div>
                              <p className="text-white/60 text-sm">Followers</p>
                              <p className="text-white text-lg font-semibold">
                                {builder.followers}
                              </p>
                            </div>
                          </div>

                          <div>
                            <p className="text-white/60 text-sm mb-2">
                              Projects
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {builder.projects.map((project, index) => (
                                <Badge
                                  key={index}
                                  variant="outline"
                                  className="border-white/20 text-white/80"
                                >
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
    </>
  );
}
