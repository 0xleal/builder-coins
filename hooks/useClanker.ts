"use client";

import { usePrivy } from "@privy-io/react-auth";
import { useAccount, useWalletClient } from "wagmi";
import { createPublicClient, http } from "viem";
import { Clanker } from "clanker-sdk/v4";
import { baseSepolia } from "viem/chains";

const PAIRED_TOKEN = process.env
  .NEXT_PUBLIC_LIQUIDITY_TOKEN_ADDRESS as `0x${string}`;

export const useClanker = () => {
  const { ready, authenticated } = usePrivy();
  const account = useAccount();
  const { data: walletClient } = useWalletClient(account);
  const client = createPublicClient({ chain: baseSepolia, transport: http() });

  const clanker = new Clanker({
    // @ts-ignore, TODO: fix this
    publicClient: client,
    wallet: walletClient,
  });

  const handleDeploy = async (name: string, symbol: string) => {
    if (!ready) {
      throw new Error("Not ready");
    }
    if (!authenticated) {
      throw new Error("Not authenticated");
    }

    const { txHash, waitForTransaction, error } = await clanker.deploy({
      name,
      symbol,
      type: "v4",
      tokenAdmin: account.address as `0x${string}`,
      vanity: true,
      pool: {
        pairedToken: PAIRED_TOKEN,
        positions: [
          {
            tickLower: -921000,
            tickUpper: -900000,
            positionBps: 1500,
          },
          {
            tickLower: -900000,
            tickUpper: -800000,
            positionBps: 1500,
          },
          {
            tickLower: -800000,
            tickUpper: -600000,
            positionBps: 1500,
          },
          {
            tickLower: -600000,
            tickUpper: -400000,
            positionBps: 1500,
          },
          {
            tickLower: -400000,
            tickUpper: -200000,
            positionBps: 1500,
          },
          {
            tickLower: -200000,
            tickUpper: 0,
            positionBps: 1000,
          },
        ],
      },
    });

    if (error) throw error;
    const { address } = await waitForTransaction();
    console.log(
      `Deployed token to ${address} on chain ${baseSepolia.id}, tx hash: ${txHash}`
    );
    return { address, txHash };
  };

  return { handleDeploy };
};
