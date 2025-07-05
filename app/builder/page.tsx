"use client";

import type React from "react";

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
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Rocket,
  Users,
  TrendingUp,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { useClanker } from "@/hooks/useClanker";

export default function BuilderPage() {
  const [tokenName, setTokenName] = useState("BuilderCoin Leal");
  const [tokenTicker, setTokenTicker] = useState("LEAL");
  const [description, setDescription] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(true);
  const [tokenAddress, setTokenAddress] = useState<`0x${string}` | undefined>(
    "0x869A5b968155a2137C1a6Fd277ebAf47384134E1"
  );
  const [txHash, setTxHash] = useState<`0x${string}` | undefined>(
    "0xcd05776c4ef6874b9fef1438d116533083eab1a021f059d1d1af180c06ba8bdd"
  );
  const { handleDeploy } = useClanker();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    if (!tokenName || !tokenTicker || !description) {
      return;
    }

    try {
      const { address, txHash } = await handleDeploy(
        tokenName,
        tokenTicker,
        description
      );
      handleRecordDeployment();
      setIsSuccess(true);
      setTokenAddress(address);
      setTxHash(txHash);
    } catch (error) {
      console.error(error);
    }

    setIsSubmitting(false);
  };

  const handleRecordDeployment = async () => {
    if (!txHash) return;

    try {
      const response = await fetch("/api/token-deployment", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          deployment_tx_hash: txHash,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        console.error(`Error: ${error.error}`);
      }
    } catch (error) {
      console.error("Error recording deployment:", error);
    }
  };

  if (isSuccess) {
    return (
      <>
        <div className="container mx-auto px-4 py-20">
          <div className="max-w-2xl mx-auto text-center">
            <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-10 w-10 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-white mb-4">
              Token Launched Successfully!
            </h1>
            <p className="text-white/80 text-lg mb-8">
              Congratulations! Your token <strong>${tokenTicker}</strong> has
              been created and is now live on the blockchain.
            </p>

            <Card className="bg-white/5 border-white/10 backdrop-blur-sm mb-8">
              <CardContent className="p-6">
                <div className="grid grid-cols-2 gap-4 text-left">
                  <div>
                    <p className="text-white/60 text-sm">Token Name</p>
                    <p className="text-white font-semibold">{tokenName}</p>
                  </div>
                  <div>
                    <p className="text-white/60 text-sm">Token Ticker</p>
                    <p className="text-white font-semibold">${tokenTicker}</p>
                  </div>
                  <div>
                    <p className="text-white/60 text-sm">Token Address</p>
                    <p className="text-white font-semibold">
                      <a
                        href={`https://basescan.org/address/${tokenAddress}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {tokenAddress?.slice(0, 6)}...{tokenAddress?.slice(-4)}
                      </a>
                    </p>
                  </div>
                  <div>
                    <p className="text-white/60 text-sm">Transaction Hash</p>
                    <p className="text-white font-semibold">
                      <a
                        href={`https://basescan.org/tx/${txHash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {txHash?.slice(0, 6)}...{txHash?.slice(-4)}
                      </a>
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Alert className="bg-blue-500/20 border-blue-500/30 mb-8">
              <AlertCircle className="h-4 w-4 text-blue-400" />
              <AlertDescription className="text-blue-200">
                Your token is now eligible for consideration by our AI fund
                manager. The algorithm will analyze your token&apos;s
                performance and community engagement to determine if it should
                be included in the fund.
              </AlertDescription>
            </Alert>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/fund">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white px-8 py-3"
                >
                  View Fund
                </Button>
              </Link>
              <Button
                size="lg"
                variant="outline"
                className="border-white/20 text-white hover:bg-white/10 px-8 py-3 bg-transparent"
              >
                Share Your Token
              </Button>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-white mb-4">
              Launch Your Builder Token
            </h1>
            <p className="text-white/80 text-lg">
              Join the decentralized builder economy by creating your personal
              token
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Form */}
            <div className="lg:col-span-2">
              <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white flex items-center">
                    <Rocket className="mr-2 h-5 w-5" />
                    Token Details
                  </CardTitle>
                  <CardDescription className="text-white/70">
                    Provide the basic information for your builder token
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-2">
                      <Label htmlFor="token-name" className="text-white">
                        Token Name
                      </Label>
                      <Input
                        id="token-name"
                        placeholder="e.g., Alex Chen Token"
                        value={tokenName}
                        onChange={(e) => setTokenName(e.target.value)}
                        className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                        required
                      />
                      <p className="text-white/60 text-sm">
                        The full name of your token
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="token-ticker" className="text-white">
                        Token Ticker
                      </Label>
                      <Input
                        id="token-ticker"
                        placeholder="e.g., ALEX"
                        value={tokenTicker}
                        onChange={(e) =>
                          setTokenTicker(e.target.value.toUpperCase())
                        }
                        className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                        maxLength={6}
                        required
                      />
                      <p className="text-white/60 text-sm">
                        3-6 characters, will be prefixed with $
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="description" className="text-white">
                        Description
                      </Label>
                      <Textarea
                        id="description"
                        placeholder="Tell the community about yourself and what you're building..."
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        className="bg-white/10 border-white/20 text-white placeholder:text-white/50 min-h-[100px]"
                        required
                      />
                      <p className="text-white/60 text-sm">
                        Describe your background and projects
                      </p>
                    </div>

                    <Button
                      type="submit"
                      className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-3"
                      disabled={
                        isSubmitting ||
                        !tokenName ||
                        !tokenTicker ||
                        !description
                      }
                    >
                      {isSubmitting ? "Launching Token..." : "Launch Token"}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </div>

            {/* Info Sidebar */}
            <div className="space-y-6">
              <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white text-lg">
                    Token Economics
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Your Allocation</span>
                    <span className="text-white font-semibold">50%</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-white/70">Liquidity Pool</span>
                    <span className="text-white font-semibold">50%</span>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="text-white text-lg">
                    Requirements
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-start space-x-3">
                    <Users className="h-5 w-5 text-blue-400 mt-0.5" />
                    <div>
                      <p className="text-white font-medium">
                        Community Building
                      </p>
                      <p className="text-white/70 text-sm">
                        Engage with holders and build your reputation
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <TrendingUp className="h-5 w-5 text-purple-400 mt-0.5" />
                    <div>
                      <p className="text-white font-medium">
                        Fund Consideration
                      </p>
                      <p className="text-white/70 text-sm">
                        AI algorithm evaluates tokens for fund inclusion
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Alert className="bg-blue-500/20 border-blue-500/30">
                <AlertCircle className="h-4 w-4 text-blue-400" />
                <AlertDescription className="text-blue-200">
                  Once launched, your token will be evaluated by our AI fund
                  manager for potential inclusion in the Builders Fund
                  portfolio.
                </AlertDescription>
              </Alert>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
