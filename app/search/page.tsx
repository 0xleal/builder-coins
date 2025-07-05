"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Search,
  Filter,
  TrendingUp,
  TrendingDown,
  Loader2,
} from "lucide-react";
import { useTokensWithSearch } from "@/hooks/useTokens";
import { useDebounce } from "use-debounce";

const categories = [
  "All",
  "DeFi",
  "Security",
  "NFT",
  "Infrastructure",
  "Gaming",
  "AI",
  "Token",
  "Blockchain",
];
const sortOptions = [
  { value: "marketCap", label: "Market Cap" },
  { value: "currentPrice", label: "Price" },
  { value: "change24h", label: "24h Change" },
  { value: "volume24h", label: "Volume" },
  { value: "holders", label: "Holders" },
  { value: "socialScore", label: "Social Score" },
  { value: "launchDate", label: "Launch Date" },
];

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [sortBy, setSortBy] = useState("marketCap");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [showInFundOnly, setShowInFundOnly] = useState(false);
  const [showVerifiedOnly, setShowVerifiedOnly] = useState(false);
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");

  // Debounce search query to avoid too many API calls
  const [debouncedSearchQuery] = useDebounce(searchQuery, 300);

  // Use the new search hook with all filters
  const {
    data: filteredAndSortedBuilders = [],
    isLoading,
    error,
  } = useTokensWithSearch({
    searchQuery: debouncedSearchQuery,
    category: selectedCategory,
    minPrice: minPrice ? Number.parseFloat(minPrice) : undefined,
    maxPrice: maxPrice ? Number.parseFloat(maxPrice) : undefined,
    showInFundOnly,
    showVerifiedOnly,
    sortBy,
    sortOrder,
    first: 100, // Limit results
  });

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return `$${(num / 1000000).toFixed(2)}M`;
    } else if (num >= 1000) {
      return `$${(num / 1000).toFixed(1)}K`;
    }
    return `$${num.toFixed(2)}`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Search Builders
          </h1>
          <p className="text-white/80 text-lg">
            Discover and explore Web3 builders in the ecosystem
          </p>
        </div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1">
            <Card className="bg-white/5 border-white/10 backdrop-blur-sm sticky top-4">
              <CardHeader>
                <CardTitle className="text-white flex items-center">
                  <Filter className="mr-2 h-5 w-5" />
                  Filters
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Search Input */}
                <div className="space-y-2">
                  <Label className="text-white">Search</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-white/50" />
                    <Input
                      placeholder="Search builders, tokens, tags..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-white/50"
                    />
                  </div>
                </div>

                {/* Category Filter */}
                <div className="space-y-2">
                  <Label className="text-white">Category</Label>
                  <Select
                    value={selectedCategory}
                    onValueChange={setSelectedCategory}
                  >
                    <SelectTrigger className="bg-white/10 border-white/20 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-white/20">
                      {categories.map((category) => (
                        <SelectItem
                          key={category}
                          value={category}
                          className="text-white"
                        >
                          {category}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Price Range */}
                <div className="space-y-2">
                  <Label className="text-white">Price Range</Label>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Min"
                      type="number"
                      value={minPrice}
                      onChange={(e) => setMinPrice(e.target.value)}
                      className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                    />
                    <Input
                      placeholder="Max"
                      type="number"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      className="bg-white/10 border-white/20 text-white placeholder:text-white/50"
                    />
                  </div>
                </div>

                {/* Checkboxes */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="in-fund"
                      checked={showInFundOnly}
                      onCheckedChange={(checked) =>
                        setShowInFundOnly(
                          checked === "indeterminate" ? false : checked
                        )
                      }
                      className="border-white/20 data-[state=checked]:bg-green-600 data-[state=checked]:border-green-600"
                    />
                    <Label
                      htmlFor="in-fund"
                      className="text-white/80 cursor-pointer"
                    >
                      In Fund Only
                    </Label>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="verified"
                      checked={showVerifiedOnly}
                      onCheckedChange={(checked) =>
                        setShowVerifiedOnly(
                          checked === "indeterminate" ? false : checked
                        )
                      }
                      className="border-white/20 data-[state=checked]:bg-blue-600 data-[state=checked]:border-blue-600"
                    />
                    <Label
                      htmlFor="verified"
                      className="text-white/80 cursor-pointer"
                    >
                      Verified Only
                    </Label>
                  </div>
                </div>

                {/* Clear Filters */}
                <Button
                  variant="outline"
                  onClick={() => {
                    setSearchQuery("");
                    setSelectedCategory("All");
                    setShowInFundOnly(false);
                    setShowVerifiedOnly(false);
                    setMinPrice("");
                    setMaxPrice("");
                  }}
                  className="w-full border-white/20 text-white hover:bg-white/10 bg-transparent"
                >
                  Clear Filters
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Results */}
          <div className="lg:col-span-3">
            {/* Sort Controls */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
              <div className="text-white">
                <span className="text-lg font-semibold">
                  {filteredAndSortedBuilders.length}
                  {filteredAndSortedBuilders.length === 100 ? "+" : ""}
                </span>
                <span className="text-white/70 ml-1">builders found</span>
              </div>

              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <Label className="text-white text-sm">Sort by:</Label>
                  <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-40 bg-white/10 border-white/20 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-white/20">
                      {sortOptions.map((option) => (
                        <SelectItem
                          key={option.value}
                          value={option.value}
                          className="text-white"
                        >
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    setSortOrder(sortOrder === "asc" ? "desc" : "asc")
                  }
                  className="border-white/20 text-white hover:bg-white/10 bg-transparent"
                >
                  {sortOrder === "asc" ? (
                    <TrendingUp className="h-4 w-4" />
                  ) : (
                    <TrendingDown className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>

            {/* Loading State */}
            {isLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-white" />
                <span className="ml-2 text-white">Loading tokens...</span>
              </div>
            )}

            {/* Error State */}
            {error && (
              <Card className="bg-red-500/10 border-red-500/20 backdrop-blur-sm">
                <CardContent className="p-12 text-center">
                  <div className="text-red-400 mb-4">⚠️</div>
                  <h3 className="text-white text-lg font-semibold mb-2">
                    Error Loading Tokens
                  </h3>
                  <p className="text-white/70">
                    {error.message ||
                      "Failed to load tokens from the GraphQL endpoint"}
                  </p>
                </CardContent>
              </Card>
            )}

            {/* Builder Cards */}
            {!isLoading && !error && (
              <div className="space-y-4">
                {filteredAndSortedBuilders.map((builder) => (
                  <Card
                    key={builder.id}
                    className="bg-white/5 border-white/10 backdrop-blur-sm hover:bg-white/10 transition-colors"
                  >
                    <CardContent className="p-6">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start space-x-4 flex-1">
                          <Avatar className="w-16 h-16">
                            <AvatarImage
                              src={builder.profileImage || "/placeholder.svg"}
                              alt={builder.profileName}
                            />
                            <AvatarFallback className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                              {builder.profileName
                                .split(" ")
                                .map((n: string) => n[0])
                                .join("")}
                            </AvatarFallback>
                          </Avatar>

                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="text-white font-semibold text-lg">
                                {builder.profileName}
                              </h3>
                              {builder.verified && (
                                <div className="w-2 h-2 bg-blue-400 rounded-full" />
                              )}
                              <Badge
                                variant="secondary"
                                className="bg-white/10 text-white/80"
                              >
                                ${builder.tokenSymbol}
                              </Badge>
                              {builder.inFund && (
                                <Badge className="bg-green-600 text-white">
                                  In Fund ({builder.fundAllocation}%)
                                </Badge>
                              )}
                            </div>

                            <div className="flex flex-wrap gap-2 mb-4">
                              {builder.tags.map((tag: string) => (
                                <Badge
                                  key={tag}
                                  variant="outline"
                                  className="border-white/20 text-white/70"
                                >
                                  {tag}
                                </Badge>
                              ))}
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                              <div>
                                <p className="text-white/60">Price</p>
                                <p className="text-white font-semibold">
                                  ${builder.currentPrice.toFixed(2)}
                                </p>
                              </div>
                              <div>
                                <p className="text-white/60">Market Cap</p>
                                <p className="text-white font-semibold">
                                  {formatNumber(builder.marketCap)}
                                </p>
                              </div>
                              <div>
                                <p className="text-white/60">24h Change</p>
                                <p
                                  className={`font-semibold ${
                                    builder.change24h >= 0
                                      ? "text-green-400"
                                      : "text-red-400"
                                  }`}
                                >
                                  {builder.change24h >= 0 ? "+" : ""}
                                  {builder.change24h.toFixed(2)}%
                                </p>
                              </div>
                              <div>
                                <p className="text-white/60">Holders</p>
                                <p className="text-white font-semibold">
                                  {builder.holders.toLocaleString()}
                                </p>
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-col items-end space-y-2">
                          <div className="text-right">
                            <p className="text-white/60 text-sm">
                              Social Score
                            </p>
                            <p className="text-white font-semibold">
                              {builder.socialScore}/100
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-white/60 text-sm">Launched</p>
                            <p className="text-white text-sm">
                              {formatDate(builder.launchDate)}
                            </p>
                          </div>
                          <Link
                            href={`/builder/${builder.tokenAddress.toLowerCase()}`}
                          >
                            <Button
                              size="sm"
                              className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white"
                            >
                              View Profile
                            </Button>
                          </Link>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {filteredAndSortedBuilders.length === 0 && (
                  <Card className="bg-white/5 border-white/10 backdrop-blur-sm">
                    <CardContent className="p-12 text-center">
                      <Search className="h-12 w-12 text-white/40 mx-auto mb-4" />
                      <h3 className="text-white text-lg font-semibold mb-2">
                        No builders found
                      </h3>
                      <p className="text-white/70">
                        Try adjusting your search criteria or filters
                      </p>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
