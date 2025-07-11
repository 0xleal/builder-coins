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
  priceChangePercentage24h: number;

  // Fund status
  fundStatus: {
    inFund: boolean;
    allocation: number;
    investmentDate: string;
    initialPrice: number;
    currentReturn: number;
  };
};

export type DexscreenerResponse = {
  pair: {
    priceUsd: number;
    volume: {
      h24: number;
      h6: number;
      h1: number;
      m5: number;
    };
    priceChange: {
      h24: number;
    };
    fdv: number;
    marketCap: number;
    url: string;
    priceNative: number;
  };
};

export type FundManagerPortfolio = {
  wallet_address: string;
  balances: {
    value_usd: number;
    chain: string;
    chain_id: number;
    address: string;
    amount: string;
    symbol: string;
    decimals: number;
    price_usd: number;
  }[];
  value: number;
  liquidity_available: number;
  builder_coins_held: number;
};

export type FundManagerAllocation = {
  token_address: string;
  allocation_percentage: number;
  builder_score: number;
  deployer_address: string;
};
