import { useQuery } from "@tanstack/react-query";

const GRAPHQL_ENDPOINT =
  "https://api.studio.thegraph.com/query/8098/builder-coins-ethglobal-cannes/version/latest";

export interface TokenCreated {
  id: string;
  msgSender: string;
  tokenAddress: string;
  tokenAdmin: string;
  tokenImage: string;
  tokenName: string;
  tokenSymbol: string;
  tokenMetadata: string;
  tokenContext: string;
  startingTick: number;
  poolHook: string;
  poolId: string;
  pairedToken: string;
  locker: string;
  mevModule: string;
  extensionsSupply: string;
  extensions: string[];
  blockNumber: string;
  blockTimestamp: string;
  transactionHash: string;
}

export interface Builder {
  id: string;
  profileName: string;
  tokenSymbol: string;
  tokenName: string;
  profileImage: string;
  description: string;
  currentPrice: number;
  marketCap: number;
  change24h: number;
  change7d: number;
  volume24h: number;
  holders: number;
  category: string;
  tags: string[];
  inFund: boolean;
  fundAllocation: number;
  verified: boolean;
  launchDate: string;
  projects: string[];
  socialScore: number;
  tokenAddress: string;
  creator: string;
}

export interface SearchFilters {
  searchQuery?: string;
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  showInFundOnly?: boolean;
  showVerifiedOnly?: boolean;
  sortBy?: string;
  sortOrder?: "asc" | "desc";
  first?: number;
  skip?: number;
}

const GET_TOKENS_QUERY = `
  query GetTokens($first: Int, $skip: Int, $orderBy: String, $orderDirection: String) {
    tokenCreateds(
      first: $first
      skip: $skip
      orderBy: $orderBy
      orderDirection: $orderDirection
    ) {
      id
      msgSender
      tokenAddress
      tokenAdmin
      tokenImage
      tokenName
      tokenSymbol
      tokenMetadata
      tokenContext
      startingTick
      poolHook
      poolId
      pairedToken
      locker
      mevModule
      extensionsSupply
      extensions
      blockNumber
      blockTimestamp
      transactionHash
    }
  }
`;

// Enhanced query with search filtering
const GET_TOKENS_WITH_SEARCH_QUERY = `
  query GetTokensWithSearch(
    $first: Int, 
    $skip: Int, 
    $orderBy: String, 
    $orderDirection: String,
    $tokenName_contains_nocase: String,
    $tokenSymbol_contains_nocase: String
  ) {
    tokenCreateds(
      first: $first
      skip: $skip
      orderBy: $orderBy
      orderDirection: $orderDirection
      where: {
        or: [
          { tokenName_contains_nocase: $tokenName_contains_nocase }
          { tokenSymbol_contains_nocase: $tokenSymbol_contains_nocase }
        ]
      }
    ) {
      id
      msgSender
      tokenAddress
      tokenAdmin
      tokenImage
      tokenName
      tokenSymbol
      tokenMetadata
      tokenContext
      startingTick
      poolHook
      poolId
      pairedToken
      locker
      mevModule
      extensionsSupply
      extensions
      blockNumber
      blockTimestamp
      transactionHash
    }
  }
`;

async function fetchTokens(variables: any = {}): Promise<TokenCreated[]> {
  const response = await fetch(GRAPHQL_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: GET_TOKENS_QUERY,
      variables: {
        first: 100,
        skip: 0,
        orderBy: "blockTimestamp",
        orderDirection: "desc",
        ...variables,
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`GraphQL request failed: ${response.status}`);
  }

  const data = await response.json();

  if (data.errors) {
    throw new Error(
      `GraphQL errors: ${data.errors.map((e: any) => e.message).join(", ")}`
    );
  }

  return data.data.tokenCreateds;
}

async function fetchTokensWithSearch(
  variables: any = {}
): Promise<TokenCreated[]> {
  const { searchQuery, ...otherVariables } = variables;

  // Use the enhanced query only if we have a search query
  const query = searchQuery ? GET_TOKENS_WITH_SEARCH_QUERY : GET_TOKENS_QUERY;

  const queryVariables = {
    first: 100,
    skip: 0,
    orderBy: "blockTimestamp",
    orderDirection: "desc",
    ...otherVariables,
  };

  // Add search variables if we have a search query
  if (searchQuery) {
    queryVariables.tokenName_contains_nocase = searchQuery;
    queryVariables.tokenSymbol_contains_nocase = searchQuery;
  }

  const response = await fetch(GRAPHQL_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      variables: queryVariables,
    }),
  });

  if (!response.ok) {
    throw new Error(`GraphQL request failed: ${response.status}`);
  }

  const data = await response.json();

  if (data.errors) {
    throw new Error(
      `GraphQL errors: ${data.errors.map((e: any) => e.message).join(", ")}`
    );
  }

  return data.data.tokenCreateds;
}

// Transform GraphQL data to Builder format
function transformTokenToBuilder(token: TokenCreated): Builder {
  // Parse metadata if it's JSON
  let metadata: any = {};
  try {
    if (token.tokenMetadata) {
      metadata = JSON.parse(token.tokenMetadata);
    }
  } catch (e) {
    // If parsing fails, use empty object
  }

  // Parse context if it's JSON
  let context: any = {};
  try {
    if (token.tokenContext) {
      context = JSON.parse(token.tokenContext);
    }
  } catch (e) {
    // If parsing fails, use empty object
  }

  // Generate mock data for fields not available in GraphQL
  const mockData = {
    currentPrice: Math.random() * 20 + 1,
    marketCap: Math.random() * 2000000 + 100000,
    change24h: (Math.random() - 0.5) * 20,
    change7d: (Math.random() - 0.5) * 40,
    volume24h: Math.random() * 100000 + 10000,
    holders: Math.floor(Math.random() * 5000) + 100,
    socialScore: Math.floor(Math.random() * 40) + 60,
  };

  return {
    id: token.id,
    profileName: token.tokenName,
    tokenSymbol: token.tokenSymbol,
    tokenName: token.tokenName,
    profileImage: token.tokenImage || "/placeholder.svg",
    description:
      context.description ||
      token.tokenContext ||
      "Token created on the blockchain",
    currentPrice: mockData.currentPrice,
    marketCap: mockData.marketCap,
    change24h: mockData.change24h,
    change7d: mockData.change7d,
    volume24h: mockData.volume24h,
    holders: mockData.holders,
    category: metadata.category || context.category || "DeFi",
    tags: metadata.tags || context.tags || ["Token", "Blockchain"],
    inFund: Math.random() > 0.6, // 40% chance of being in fund
    fundAllocation: Math.random() * 10,
    verified: Math.random() > 0.7, // 30% chance of being verified
    launchDate: new Date(parseInt(token.blockTimestamp) * 1000)
      .toISOString()
      .split("T")[0],
    projects: metadata.projects || context.projects || [],
    socialScore: mockData.socialScore,
    tokenAddress: token.tokenAddress,
    creator: token.msgSender,
  };
}

// Apply client-side filters for fields that can't be filtered server-side
function applyClientSideFilters(
  builders: Builder[],
  filters: SearchFilters
): Builder[] {
  return builders.filter((builder) => {
    // Additional text search in description and tags (since these are derived from JSON)
    if (filters.searchQuery) {
      const searchLower = filters.searchQuery.toLowerCase();
      const matchesDescription = builder.description
        .toLowerCase()
        .includes(searchLower);
      const matchesTags = builder.tags.some((tag) =>
        tag.toLowerCase().includes(searchLower)
      );

      // If already matches name/symbol from server-side query, or matches description/tags
      if (!(matchesDescription || matchesTags)) {
        // Since server-side already filtered name/symbol, we only need to exclude if it doesn't match description/tags
        const matchesNameSymbol =
          builder.profileName.toLowerCase().includes(searchLower) ||
          builder.tokenSymbol.toLowerCase().includes(searchLower);

        if (!matchesNameSymbol) {
          return false;
        }
      }
    }

    // Category filter
    if (
      filters.category &&
      filters.category !== "All" &&
      builder.category !== filters.category
    ) {
      return false;
    }

    // Price range filter
    if (
      filters.minPrice !== undefined &&
      builder.currentPrice < filters.minPrice
    ) {
      return false;
    }
    if (
      filters.maxPrice !== undefined &&
      builder.currentPrice > filters.maxPrice
    ) {
      return false;
    }

    // Fund filter
    if (filters.showInFundOnly && !builder.inFund) {
      return false;
    }

    // Verified filter
    if (filters.showVerifiedOnly && !builder.verified) {
      return false;
    }

    return true;
  });
}

// Sort builders based on sort criteria
function sortBuilders(
  builders: Builder[],
  sortBy: string,
  sortOrder: "asc" | "desc"
): Builder[] {
  const sorted = [...builders];

  sorted.sort((a, b) => {
    let aValue: any = a[sortBy as keyof Builder];
    let bValue: any = b[sortBy as keyof Builder];

    // Handle date sorting
    if (sortBy === "launchDate") {
      aValue = new Date(aValue).getTime();
      bValue = new Date(bValue).getTime();
    }

    if (sortOrder === "asc") {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  return sorted;
}

export function useTokens() {
  return useQuery({
    queryKey: ["tokens"],
    queryFn: fetchTokens,
    select: (data: TokenCreated[]) => data.map(transformTokenToBuilder),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // 30 seconds
  });
}

export function useTokensWithFilters(filters: {
  orderBy?: string;
  orderDirection?: "asc" | "desc";
  first?: number;
  skip?: number;
}) {
  return useQuery({
    queryKey: ["tokens", filters],
    queryFn: () => fetchTokens(filters),
    select: (data: TokenCreated[]) => data.map(transformTokenToBuilder),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 30 * 1000, // 30 seconds
  });
}

export function useTokensWithSearch(filters: SearchFilters) {
  return useQuery({
    queryKey: ["tokens", "search", filters],
    queryFn: () => fetchTokensWithSearch(filters),
    select: (data: TokenCreated[]) => {
      const builders = data.map(transformTokenToBuilder);
      const filtered = applyClientSideFilters(builders, filters);

      if (filters.sortBy) {
        return sortBuilders(
          filtered,
          filters.sortBy,
          filters.sortOrder || "desc"
        );
      }

      return filtered;
    },
    staleTime: 2 * 60 * 1000, // 2 minutes for search results
    enabled: true, // Always enabled, but can be controlled by the component
  });
}
