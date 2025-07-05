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
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
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
import { TALENT_TOKEN } from "@/lib/constants";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { useWallets } from "@privy-io/react-auth";
import { createWalletClient, custom } from "viem";
import { addEnsContracts } from "@ensdomains/ensjs";
import { setRecords } from "@ensdomains/ensjs/wallet";

export default function BuilderDetails({
  builder,
}: {
  builder: Builder | null;
}) {
  const [copied, setCopied] = useState("");
  const [tradeModalOpen, setTradeModalOpen] = useState(false);

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
  const { wallets } = useWallets();
  const wallet = wallets.find(
    (w) => w.address.toLowerCase() === builder?.deployerAddress?.toLowerCase()
  );

  if (!builder || !wallet) {
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

  const setTokenOnEnsRecord = async () => {
    if (!wallet) return;

    await wallet.switchChain(mainnet.id);
    const provider = await wallet.getEthereumProvider();

    const walletClient = createWalletClient({
      chain: addEnsContracts(mainnet),
      transport: custom(provider),
    });
    const hash = await setRecords(walletClient, {
      name: ensName as string,
      account: wallet.address as `0x${string}`,
      texts: [
        {
          key: "BuilderCoin",
          value: `https://builder-coins.vercel.app/builder/${builder.tokenAddress}`,
        },
      ],
      resolverAddress: "0x231b0Ee14048e9dCcD1d247744d114a4EB5E8E63",
    });
    console.log(hash);

    return hash;
  };

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

  const calculateTokenAddress = (token: string) => {
    if (token === "ETH") return "0x0000000000000000000000000000000000000000";
    if (token === "TALENT") return TALENT_TOKEN.address;
    return builder.tokenAddress;
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
              {builder.fundStatus.inFund && (
                <CheckCircle className="h-6 w-6 text-blue-400" />
              )}
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
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
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
                    <p className="text-white/60 text-sm">Price Change 24h</p>
                    <p className="text-white text-xl font-bold">
                      {builder.priceChangePercentage24h.toFixed(2)}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Chart */}
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm mb-8">
              <CardContent>
                <div id="dexscreener-embed">
                  <iframe src="https://dexscreener.com/base/0x06ba5105a1046f706f705b8837a777cfc5843e7141244390c5bea5d1d990593e?embed=1&loadChartSettings=0&trades=0&tabs=0&info=0&chartLeftToolbar=0&chartDefaultOnMobile=1&chartTheme=dark&theme=dark&chartStyle=0&chartType=usd&interval=15"></iframe>
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
                  Buy and sell ${builder.tokenSymbol}
                </CardTitle>
                <CardDescription className="text-white/70">
                  Participate in ${builder.tokenSymbol} economy
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                  onClick={() => setTradeModalOpen(true)}
                >
                  Swap Tokens
                </Button>
              </CardContent>
            </Card>
            <Dialog open={tradeModalOpen} onOpenChange={setTradeModalOpen}>
              <DialogContent className="bg-slate-900 border-white/10 text-white max-w-2xl max-h-[80vh] min-h-[60vh] overflow-y-auto">
                <iframe
                  src={`https://app.uniswap.org/swap?inputCurrency=${calculateTokenAddress(
                    "TALENT"
                  )}&outputCurrency=${builder.tokenAddress}&chain=base`}
                  className="w-full h-full"
                ></iframe>
              </DialogContent>
            </Dialog>

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
                {wallet && (
                  <Button
                    onClick={setTokenOnEnsRecord}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                  >
                    Set Token on ENS Record
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </>
  );
}
