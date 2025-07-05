import { Token, ChainId } from "@uniswap/sdk-core";

export const QUOTER_CONTRACT_ADDRESS =
  "0x0d5e0f971ed27fbff6c2837bf31316121532048d";
const TALENT_TOKEN_ADDRESS = process.env
  .NEXT_PUBLIC_LIQUIDITY_TOKEN_ADDRESS! as `0x${string}`;

export const ETH_TOKEN = new Token(
  ChainId.BASE,
  "0x0000000000000000000000000000000000000000",
  18,
  "ETH",
  "Ether"
);

export const TALENT_TOKEN = new Token(
  ChainId.BASE,
  TALENT_TOKEN_ADDRESS,
  18,
  "TALENT",
  "TalentProtocolToken"
);

export const DEXSCREENER_BASE_URL =
  "https://api.dexscreener.com/latest/dex/pairs/base";

export const FUND_MANAGER_ADDRESS = process.env
  .NEXT_PUBLIC_FUND_MANAGER_ADDRESS! as `0x${string}`;
