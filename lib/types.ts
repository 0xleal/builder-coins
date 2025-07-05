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

  // Fund status
  fundStatus: {
    inFund: boolean;
    allocation: number;
    investmentDate: string;
    initialPrice: number;
    currentReturn: number;
  };
};
