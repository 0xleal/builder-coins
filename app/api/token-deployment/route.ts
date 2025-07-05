import { NextRequest, NextResponse } from "next/server";
import { PrivyClient } from "@privy-io/server-auth";
import { createClient } from "@supabase/supabase-js";
import { createPublicClient, http, decodeEventLog } from "viem";
import { base } from "viem/chains";
import ClankerDeployer from "@/lib/abi/ClankerDeployer.json";

const PRIVY_APP_ID = process.env.NEXT_PUBLIC_PRIVY_APP_ID!;
const PRIVY_APP_SECRET = process.env.PRIVY_APP_SECRET!;
const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_KEY = process.env.SUPABASE_KEY!;

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY);

// Create viem client for Base chain
const client = createPublicClient({
  chain: base,
  transport: http(),
});

// Event signature for token deployment
const DEPLOYMENT_EVENT_TOPIC =
  "0x9299d1d1a88d8e1abdc591ae7a167a6bc63a8f17d695804e9091ee33aa89fb67";

// TypeScript interface for TokenCreated event arguments
interface TokenCreatedEventArgs {
  msgSender: `0x${string}`;
  tokenAddress: `0x${string}`;
  tokenAdmin: `0x${string}`;
  tokenImage: string;
  tokenName: string;
  tokenSymbol: string;
  tokenMetadata: string;
  tokenContext: string;
  startingTick: bigint;
  poolHook: `0x${string}`;
  poolId: `0x${string}`;
  pairedToken: `0x${string}`;
  locker: `0x${string}`;
  mevModule: `0x${string}`;
  extensionsSupply: bigint;
  extensions: readonly `0x${string}`[];
}

async function extractDeploymentData(txHash: string) {
  try {
    // Get transaction receipt using client method
    const receipt = await client.getTransactionReceipt({
      hash: txHash as `0x${string}`,
    });

    // Find the deployment event log
    const deploymentLog = receipt.logs.find(
      (log) => log.topics[0] === DEPLOYMENT_EVENT_TOPIC
    );

    if (!deploymentLog) {
      throw new Error("Deployment event not found in transaction logs");
    }

    // Decode the event log
    const decodedLog = decodeEventLog({
      abi: ClankerDeployer,
      data: deploymentLog.data,
      topics: deploymentLog.topics,
    });

    // Extract data from the decoded log args
    if (!decodedLog.args) {
      throw new Error("No args found in decoded log");
    }
    const args = decodedLog.args as unknown as TokenCreatedEventArgs;

    return {
      tokenAddress: args.tokenAddress.toLowerCase(),
      adminAddress: args.tokenAdmin.toLowerCase(),
      tokenName: args.tokenName,
      tokenSymbol: args.tokenSymbol,
      deployerAddress: args.msgSender.toLowerCase(),
      poolId: args.poolId.toLowerCase(),
      pairedToken: args.pairedToken.toLowerCase(),
      locker: args.locker.toLowerCase(),
      mevModule: args.mevModule.toLowerCase(),
      poolHook: args.poolHook.toLowerCase(),
      startingTick: args.startingTick,
      tokenMetadata: args.tokenMetadata,
      tokenImage: args.tokenImage,
      extensions: args.extensions,
      blockNumber: receipt.blockNumber,
    };
  } catch (error) {
    console.error("Error extracting deployment data:", error);
    throw error;
  }
}

export async function POST(req: NextRequest) {
  const cookieAuthToken = req.cookies.get("privy-token")?.value;
  if (!cookieAuthToken) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const privy = new PrivyClient(PRIVY_APP_ID, PRIVY_APP_SECRET);
  try {
    await privy.verifyAuthToken(cookieAuthToken);
  } catch {
    return NextResponse.json({ error: "Invalid auth token" }, { status: 401 });
  }

  let data;
  try {
    data = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }

  if (!data.deployment_tx_hash) {
    return NextResponse.json(
      { error: "Deployment tx hash is required" },
      { status: 400 }
    );
  }

  // Extract deployment data from transaction
  try {
    const deploymentData = await extractDeploymentData(data.deployment_tx_hash);

    // Create properly typed data object
    const tokenDeploymentData = {
      token_address: deploymentData.tokenAddress,
      admin_address: deploymentData.adminAddress,
      token_name: deploymentData.tokenName,
      token_symbol: deploymentData.tokenSymbol,
      deployer_address: deploymentData.deployerAddress,
      pool_id: deploymentData.poolId,
      paired_token: deploymentData.pairedToken,
      locker: deploymentData.locker,
      mev_module: deploymentData.mevModule,
      pool_hook: deploymentData.poolHook,
      starting_tick: deploymentData.startingTick,
      token_metadata: deploymentData.tokenMetadata,
      token_image: deploymentData.tokenImage,
      extensions: deploymentData.extensions,
      network: "base",
      deployment_block_number: Number(deploymentData.blockNumber),
      deployment_tx_hash: data.deployment_tx_hash,
    };

    // Duplicate detection
    const { data: existing, error: findError } = await supabase
      .from("token_deployments")
      .select("id")
      .eq("deployment_tx_hash", data.deployment_tx_hash)
      .maybeSingle();
    if (findError) {
      return NextResponse.json({ error: "Database error" }, { status: 500 });
    }
    if (existing) {
      return NextResponse.json(
        { error: "Duplicate deployment" },
        { status: 409 }
      );
    }

    // Insert with typed data
    const { error } = await supabase
      .from("token_deployments")
      .insert([tokenDeploymentData]);
    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json(
      { error: "Failed to extract deployment data from transaction" },
      { status: 400 }
    );
  }
}

// GET /api/token-deployment, returns all token deployments paginated 100 per page
export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const page = Number(searchParams.get("page")) || 1;
  const limit = Number(searchParams.get("limit")) || 100;

  const { data, error } = await supabase
    .from("token_deployments")
    .select("*")
    .order("deployment_block_number", { ascending: false })
    .range((page - 1) * limit, page * limit - 1);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  return NextResponse.json(data);
}
