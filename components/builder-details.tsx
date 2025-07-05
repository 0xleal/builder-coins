"use client";

import { useState } from "react";
import Link from "next/link";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  ArrowUpDown,
  Copy,
  CheckCircle,
  ExternalLink,
  Settings,
  Info,
} from "lucide-react";
import { Builder } from "@/lib/types";
import { useEnsAvatar, useEnsName, useEnsText } from "wagmi";
import { mainnet } from "wagmi/chains";
import Image from "next/image";

// Available tokens for swapping
const availableTokens = [
  {
    symbol: "ETH",
    name: "Ethereum",
    address: "0x0000000000000000000000000000000000000000",
    price: 2340.5,
  },
  {
    symbol: "USDC",
    name: "USD Coin",
    address: "0xA0b86a33E6441b8b4C9db4C4b8b4b8b4b8b4b8b4",
    price: 1.0,
  },
  {
    symbol: "USDT",
    name: "Tether",
    address: "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    price: 1.0,
  },
  {
    symbol: "WETH",
    name: "Wrapped Ethereum",
    address: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    price: 2340.5,
  },
];

export default function BuilderDetails({
  builder,
}: {
  builder: Builder | null;
}) {
  const [swapFromAmount, setSwapFromAmount] = useState("");
  const [swapToAmount, setSwapToAmount] = useState("");
  const [swapFromToken, setSwapFromToken] = useState("ETH");
  const [swapToToken, setSwapToToken] = useState("");
  const [copied, setCopied] = useState("");

  const { data: ensName } = useEnsName({
    address: builder?.deployerAddress as `0x${string}`,
    chainId: mainnet.id,
  });
  const { data: ensAvatar } = useEnsAvatar({
    name: ensName as string,
    chainId: mainnet.id,
  });
  const { data: bio } = useEnsText({
    name: ensName as string,
    key: "description",
    chainId: mainnet.id,
  });
  const { data: github } = useEnsText({
    name: ensName as string,
    key: "com.github",
    chainId: mainnet.id,
  });
  const { data: twitter } = useEnsText({
    name: ensName as string,
    key: "com.twitter",
    chainId: mainnet.id,
  });

  if (!builder) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white mb-4">
            Builder Not Found
          </h1>
          <Link href="/fund">
            <Button className="bg-gradient-to-r from-purple-600 to-pink-600">
              Back to Fund
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  // Set default swap to token as builder's token
  if (!swapToToken) {
    setSwapToToken(builder.tokenSymbol);
  }

  const copyToClipboard = (text: string, type: string) => {
    navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(""), 2000);
  };

  const formatAddress = (address: string) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `$${(num / 1000000).toFixed(2)}M`;
    } else if (num >= 1000) {
      return `$${(num / 1000).toFixed(1)}K`;
    }
    return `$${num.toFixed(2)}`;
  };

  const calculateSwapAmount = (
    fromAmount: string,
    fromToken: string,
    toToken: string
  ) => {
    if (!fromAmount || !fromToken || !toToken) return "0";

    const fromPrice =
      fromToken === builder.tokenSymbol
        ? builder.currentPrice
        : availableTokens.find((t) => t.symbol === fromToken)?.price || 0;
    const toPrice =
      toToken === builder.tokenSymbol
        ? builder.currentPrice
        : availableTokens.find((t) => t.symbol === toToken)?.price || 0;

    if (fromPrice === 0 || toPrice === 0) return "0";

    const result = (Number.parseFloat(fromAmount) * fromPrice) / toPrice;
    return result.toFixed(6);
  };

  const handleSwapFromChange = (value: string) => {
    setSwapFromAmount(value);
    setSwapToAmount(calculateSwapAmount(value, swapFromToken, swapToToken));
  };

  const handleSwapToChange = (value: string) => {
    setSwapToAmount(value);
    setSwapFromAmount(calculateSwapAmount(value, swapToToken, swapFromToken));
  };

  const swapTokens = () => {
    const tempToken = swapFromToken;
    const tempAmount = swapFromAmount;
    setSwapFromToken(swapToToken);
    setSwapToToken(tempToken);
    setSwapFromAmount(swapToAmount);
    setSwapToAmount(tempAmount);
  };

  return (
    <>
      {/* Cover Image */}
      <div className="h-48 bg-gradient-to-r from-purple-600/30 to-pink-600/30 relative">
        <div className="absolute inset-0 bg-black/20" />
      </div>

      <div className="container mx-auto px-4 -mt-16 relative z-10">
        {/* Profile Header */}
        <div className="flex flex-col md:flex-row items-start md:items-end space-y-4 md:space-y-0 md:space-x-6 mb-8">
          <Avatar className="w-32 h-32 border-4 border-white/20">
            <AvatarImage
              src={ensAvatar || "/placeholder.svg"}
              alt={ensName || builder.profileName}
            />
            <AvatarFallback className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-2xl">
              {ensName ||
                builder.profileName
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
            </AvatarFallback>
          </Avatar>

          <div className="flex-1">
            <div className="flex items-center space-x-3 mb-2">
              <h1 className="text-3xl font-bold text-white">
                {ensName || builder.profileName}
              </h1>
              <CheckCircle className="h-6 w-6 text-blue-400" />
              <Badge variant="secondary" className="bg-white/10 text-white/80">
                ${builder.tokenSymbol}
              </Badge>
            </div>
            {bio && <h2 className="text-xl text-white/90 mb-2">{bio}</h2>}
            <p className="text-white/80 text-lg mb-4">
              {builder.tokenMetadata.description}
            </p>

            <div className="flex flex-wrap items-center gap-4 text-white/60">
              {github && (
                <a
                  href={`https://github.com/${github}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 hover:text-white transition-colors"
                >
                  <svg
                    className="h-5 w-5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                  </svg>
                  <span>GitHub</span>
                </a>
              )}
              {twitter && (
                <a
                  href={`https://twitter.com/${twitter}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 hover:text-white transition-colors"
                >
                  <svg
                    className="h-5 w-5"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                  </svg>
                  <span>Twitter</span>
                </a>
              )}
              {ensName && (
                <a
                  href={`https://app.ens.domains/${ensName}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-2 hover:text-white transition-colors"
                >
                  <Image
                    src="/ens.svg"
                    alt="ENS"
                    width={20}
                    height={20}
                    className="h-4 w-4"
                  />
                  <span>ENS</span>
                </a>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-3">
            {builder.tokenMetadata.website && (
              <Button
                size="sm"
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10 bg-transparent"
                onClick={() =>
                  window.open(builder.tokenMetadata.website, "_blank")
                }
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
            )}
            {builder.tokenMetadata.twitter && (
              <Button
                size="sm"
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10 bg-transparent"
              >
                <span className="text-sm">𝕏</span>
              </Button>
            )}
            {builder.tokenMetadata.github && (
              <Button
                size="sm"
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10 bg-transparent"
              >
                <span className="text-sm">⚡</span>
              </Button>
            )}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Fund Status */}
            {builder.fundStatus.inFund && (
              <Card className="bg-green-500/10 border-green-500/20 backdrop-blur-sm">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-green-400 font-semibold mb-1">
                        ✅ Included in BuildersFund
                      </h3>
                      <p className="text-white/70">
                        This builder is currently part of the fund portfolio
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-semibold">
                        {builder.fundStatus.allocation}% allocation
                      </p>
                      <p className="text-green-400 text-sm">
                        +{builder.fundStatus.currentReturn}% return
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Token Contract Information */}
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Settings className="mr-2 h-5 w-5" />
                  Contract Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label className="text-white/60 text-sm">
                      Token Address
                    </Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <code className="text-white font-mono text-sm bg-white/10 px-2 py-1 rounded">
                        {formatAddress(builder.tokenAddress)}
                      </code>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          copyToClipboard(builder.tokenAddress, "token")
                        }
                        className="h-6 w-6 p-0 text-white/60 hover:text-white"
                      >
                        {copied === "token" ? (
                          <CheckCircle className="h-3 w-3" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-white/60 text-sm">
                      Admin Address
                    </Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <code className="text-white font-mono text-sm bg-white/10 px-2 py-1 rounded">
                        {formatAddress(builder.adminAddress)}
                      </code>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          copyToClipboard(builder.adminAddress, "admin")
                        }
                        className="h-6 w-6 p-0 text-white/60 hover:text-white"
                      >
                        {copied === "admin" ? (
                          <CheckCircle className="h-3 w-3" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-white/60 text-sm">
                      Deployer Address
                    </Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <code className="text-white font-mono text-sm bg-white/10 px-2 py-1 rounded">
                        {formatAddress(builder.deployerAddress)}
                      </code>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          copyToClipboard(builder.deployerAddress, "deployer")
                        }
                        className="h-6 w-6 p-0 text-white/60 hover:text-white"
                      >
                        {copied === "deployer" ? (
                          <CheckCircle className="h-3 w-3" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-white/60 text-sm">
                      Paired Token
                    </Label>
                    <div className="flex items-center space-x-2 mt-1">
                      <code className="text-white font-mono text-sm bg-white/10 px-2 py-1 rounded">
                        {formatAddress(builder.pairedToken)}
                      </code>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() =>
                          copyToClipboard(builder.pairedToken, "paired")
                        }
                        className="h-6 w-6 p-0 text-white/60 hover:text-white"
                      >
                        {copied === "paired" ? (
                          <CheckCircle className="h-3 w-3" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Token Metrics */}
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm mb-8">
              <CardHeader>
                <CardTitle className="text-white">Token Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-white/60 text-sm">Current Price</p>
                    <p className="text-white text-xl font-bold">
                      ${builder.currentPrice}
                    </p>
                  </div>
                  <div>
                    <p className="text-white/60 text-sm">Market Cap</p>
                    <p className="text-white text-xl font-bold">
                      {formatNumber(builder.marketCap)}
                    </p>
                  </div>
                  <div>
                    <p className="text-white/60 text-sm">Volume 24h</p>
                    <p className="text-white text-xl font-bold">
                      {formatNumber(builder.volume24h)}
                    </p>
                  </div>
                  <div>
                    <p className="text-white/60 text-sm">Holders</p>
                    <p className="text-white text-xl font-bold">
                      {builder.holders.toLocaleString()}
                    </p>
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-white/60">Circulating Supply</span>
                      <span className="text-white">
                        {(builder.circulatingSupply / 1000000).toFixed(1)}M /{" "}
                        {(builder.totalSupply / 1000000).toFixed(1)}M
                      </span>
                    </div>
                    <div className="w-full bg-white/10 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                        style={{
                          width: `${
                            (builder.circulatingSupply / builder.totalSupply) *
                            100
                          }%`,
                        }}
                      ></div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Token Swap Interface */}
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <ArrowUpDown className="mr-2 h-5 w-5" />
                  Token Swap
                </CardTitle>
                <CardDescription className="text-white/70">
                  Swap tokens with ${builder.tokenSymbol}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* From Token */}
                <div className="space-y-2">
                  <Label className="text-white text-sm">From</Label>
                  <div className="flex space-x-2">
                    <Select
                      value={swapFromToken}
                      onValueChange={setSwapFromToken}
                    >
                      <SelectTrigger className="w-24 bg-white/10 border-white/20 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-white/20">
                        {availableTokens.map((token) => (
                          <SelectItem
                            key={token.symbol}
                            value={token.symbol}
                            className="text-white"
                          >
                            {token.symbol}
                          </SelectItem>
                        ))}
                        <SelectItem
                          value={builder.tokenSymbol}
                          className="text-white"
                        >
                          {builder.tokenSymbol}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <Input
                      placeholder="0.0"
                      value={swapFromAmount}
                      onChange={(e) => handleSwapFromChange(e.target.value)}
                      className="flex-1 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                    />
                  </div>
                </div>

                {/* Swap Button */}
                <div className="flex justify-center">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={swapTokens}
                    className="h-8 w-8 p-0 text-white/60 hover:text-white hover:bg-white/10 rounded-full"
                  >
                    <ArrowUpDown className="h-4 w-4" />
                  </Button>
                </div>

                {/* To Token */}
                <div className="space-y-2">
                  <Label className="text-white text-sm">To</Label>
                  <div className="flex space-x-2">
                    <Select value={swapToToken} onValueChange={setSwapToToken}>
                      <SelectTrigger className="w-24 bg-white/10 border-white/20 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-800 border-white/20">
                        {availableTokens.map((token) => (
                          <SelectItem
                            key={token.symbol}
                            value={token.symbol}
                            className="text-white"
                          >
                            {token.symbol}
                          </SelectItem>
                        ))}
                        <SelectItem
                          value={builder.tokenSymbol}
                          className="text-white"
                        >
                          {builder.tokenSymbol}
                        </SelectItem>
                      </SelectContent>
                    </Select>
                    <Input
                      placeholder="0.0"
                      value={swapToAmount}
                      onChange={(e) => handleSwapToChange(e.target.value)}
                      className="flex-1 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                    />
                  </div>
                </div>

                {/* Swap Info */}
                {swapFromAmount && swapToAmount && (
                  <div className="bg-white/5 rounded-lg p-3 space-y-2 text-sm">
                    <div className="flex justify-between text-white/70">
                      <span>Exchange Rate</span>
                      <span>
                        1 {swapFromToken} ={" "}
                        {calculateSwapAmount("1", swapFromToken, swapToToken)}{" "}
                        {swapToToken}
                      </span>
                    </div>
                    <div className="flex justify-between text-white/70">
                      <span>Slippage</span>
                      <span>0.5%</span>
                    </div>
                  </div>
                )}

                <Button className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white">
                  Swap Tokens
                </Button>
              </CardContent>
            </Card>

            {/* Token Metadata */}
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Info className="mr-2 h-4 w-4" />
                  Token Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Symbol</span>
                  <span className="text-white font-semibold">
                    ${builder.tokenSymbol}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Name</span>
                  <span className="text-white font-semibold">
                    {builder.tokenName}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Total Supply</span>
                  <span className="text-white">
                    {(builder.totalSupply / 1000000).toFixed(1)}M
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-white/70">Deploy Block</span>
                  <span className="text-white">
                    #{builder.blockNumber.toLocaleString()}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}
