import { SwapExactInSingle } from "@uniswap/v4-sdk";
import { TALENT_TOKEN, ETH_TOKEN } from "./constants";
import { parseUnits } from "viem";
import { ChainId, Token } from "@uniswap/sdk-core";

export const CurrentConfig: SwapExactInSingle = {
  poolKey: {
    currency0: ETH_TOKEN.address,
    currency1: TALENT_TOKEN.address,
    fee: 500,
    tickSpacing: 10,
    hooks: "0x0000000000000000000000000000000000000000",
  },
  zeroForOne: true,
  amountIn: parseUnits("1", ETH_TOKEN.decimals).toString(),
  amountOutMinimum: "0",
  hookData: "0x00",
};

export const createConfigForToken = (
  fromTokenAddress: `0x${string}`,
  toTokenAddress: `0x${string}`,
  decimals: number,
  symbol: string,
  name: string
) => {
  const toToken = new Token(
    ChainId.BASE,
    toTokenAddress,
    decimals,
    symbol,
    name
  );
  const fromToken = new Token(
    ChainId.BASE,
    fromTokenAddress,
    decimals,
    symbol,
    name
  );

  return {
    poolKey: {
      currency0: fromToken.address,
      currency1: toToken.address,
      fee: 10000,
      tickSpacing: 200,
      hooks: "0x0000000000000000000000000000000000000000",
    },
    zeroForOne: true,
    amountIn: parseUnits("1", fromToken.decimals).toString(),
    hookData: "0x00",
  };
};
