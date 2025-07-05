import BuilderDetails from "@/components/builder-details";

export type Builder = {
  tokenAddress: string;
  adminAddress: string;
  tokenName: string;
  tokenSymbol: string;
  deployerAddress: string;
  pairedToken: string;
  tokenMetadata: {
    description: string;
    website: string;
    twitter: string;
    github: string;
    telegram: string;
  };
  blockNumber: number;
  currentPrice: number;
  profileImage: string;
  profileName: string;

  // Additional computed/display data
  marketCap: number;
  totalSupply: number;
  circulatingSupply: number;
  holders: number;
  volume24h: number;
  change24h: number;
  change7d: number;
  change30d: number;

  // Fund status
  fundStatus: {
    inFund: boolean;
    allocation: number;
    investmentDate: string;
    initialPrice: number;
    currentReturn: number;
  };
};

// Updated mock data structure to match the provided schema
const buildersData = {
  "0x742d35Cc6634C0532925a3b8D4C9db4C4b8b4b8b": {
    tokenAddress: "0x742d35Cc6634C0532925a3b8D4C9db4C4b8b4b8b",
    adminAddress: "0x8ba1f109551bD432803012645Hac136c22C4b8b8",
    tokenName: "Alex Chen Token",
    tokenSymbol: "ALEX",
    deployerAddress: "0x742d35Cc6634C0532925a3b8D4C9db4C4b8b4b8b",
    pairedToken: "0xA0b86a33E6441b8b4C9db4C4b8b4b8b4b8b4b8b4", // WETH
    tokenMetadata: {
      description:
        "Full-stack developer building the next generation of DeFi protocols with a focus on user experience and security.",
      website: "https://alexchen.dev",
      twitter: "@alexchen_dev",
      github: "alexchen",
      telegram: "@alexchen_tg",
    },
    blockNumber: 18945672,
    currentPrice: 12.34,
    profileImage: "/placeholder.svg?height=120&width=120",
    profileName: "Alex Chen",

    // Additional computed/display data
    marketCap: 1234000,
    totalSupply: 100000000,
    circulatingSupply: 75000000,
    holders: 2847,
    volume24h: 45670,
    change24h: 3.2,
    change7d: 12.8,
    change30d: 45.2,

    // Fund status
    fundStatus: {
      inFund: true,
      allocation: 8.5,
      investmentDate: "June 2024",
      initialPrice: 8.2,
      currentReturn: 50.5,
    },
  },
};

export default async function BuilderProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const builder = buildersData[id as keyof typeof buildersData] as Builder;

  return <BuilderDetails builder={builder} />;
}
