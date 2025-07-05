import { NextResponse } from "next/server";
import { NON_INVESTABLE_TOKENS } from "@/lib/constants";

const DUNE_API_URL = "https://api.sim.dune.com/v1/evm/balances";
const DUNE_API_KEY = process.env.DUNE_API_KEY!;
const FUND_MANAGER_ADDRESS = process.env.NEXT_PUBLIC_FUND_MANAGER_ADDRESS!;

export async function GET() {
  const url = `${DUNE_API_URL}/${FUND_MANAGER_ADDRESS}?chain_ids=8453`;
  const response = await fetch(url, {
    headers: {
      "X-Sim-Api-Key": DUNE_API_KEY,
    },
  });

  const data = await response.json();

  const mappedData = {
    wallet_address: data.wallet_address,
    balances: data.balances,
    liquidity_available: data.balances
      .filter((i: { address: string }) =>
        NON_INVESTABLE_TOKENS.includes(i.address.toLowerCase())
      )
      .reduce(
        (acc: number, balance: { value_usd: number }) =>
          acc + (balance.value_usd || 0),
        0
      )
      .toFixed(2),
    value: data.balances
      .filter(
        (i: { address: string }) =>
          !NON_INVESTABLE_TOKENS.includes(i.address.toLowerCase())
      )
      .reduce(
        (acc: number, balance: { value_usd: number }) =>
          acc + (balance.value_usd || 0),
        0
      )
      .toFixed(2),
    builder_coins_held: data.balances.filter(
      (i: { address: string }) =>
        !NON_INVESTABLE_TOKENS.includes(i.address.toLowerCase())
    ).length,
  };

  return NextResponse.json(mappedData);
}
