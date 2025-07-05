import { createClient } from "@supabase/supabase-js";
import { NextRequest, NextResponse } from "next/server";

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_KEY = process.env.SUPABASE_KEY!;
const DEXSCREENER_BASE_URL =
  "https://api.dexscreener.com/latest/dex/pairs/base";

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

export async function GET(req: NextRequest) {
  if (!DEXSCREENER_BASE_URL) {
    return NextResponse.json(
      { error: "DEXSCREENER_BASE_URL is not set" },
      { status: 500 }
    );
  }

  const { searchParams } = new URL(req.url);
  const tokenAddress = searchParams.get("tokenAddress");

  if (!tokenAddress) {
    return NextResponse.json(
      { error: "Token address is required" },
      { status: 400 }
    );
  }

  // fetch from supabase
  const { data: existing, error: findError } = await supabase
    .from("token_deployments")
    .select("*")
    .eq("token_address", tokenAddress)
    .maybeSingle();

  if (findError) {
    return NextResponse.json({ error: "Database error" }, { status: 500 });
  }

  if (!existing) {
    return NextResponse.json({ error: "Token not found" }, { status: 404 });
  }

  const response = await fetch(`${DEXSCREENER_BASE_URL}/${existing.pool_id}`, {
    headers: {
      "Content-Type": "application/json",
      Accept: "*/*",
    },
  });

  const data = await response.json();

  const returnData = {
    owner: existing.deployer_address,
    token_address: existing.token_address,
    token_name: existing.token_name,
    token_symbol: existing.token_symbol,
    token_decimals: existing.token_decimals,
    token_total_supply: existing.token_total_supply,
    token_metadata: existing.token_metadata,
    value_usd: data.pair.priceUsd,
    volume_usd_24h: data.pair.volume.h24,
    volume_usd_6h: data.pair.volume.h6,
    volume_usd_1h: data.pair.volume.h1,
    volume_usd_5m: data.pair.volume.m5,
    price_change_percentage_24h: data.pair.priceChange.h24,
    fdv: data.pair.fdv,
    market_cap: data.pair.marketCap,
    dexscreener_url: data.pair.url,
    value_in_base_token: data.pair.priceNative,
    base_token_address: existing.paired_token,
  };

  return NextResponse.json(returnData);
}
