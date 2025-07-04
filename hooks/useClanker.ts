"use client";

import { usePrivy, useWallets } from "@privy-io/react-auth";
import { useAccount, useWalletClient } from "wagmi";
import { createPublicClient, http } from "viem";
import { Clanker } from "clanker-sdk/v4";
import { base } from "viem/chains";

const PAIRED_TOKEN = process.env
  .NEXT_PUBLIC_LIQUIDITY_TOKEN_ADDRESS as `0x${string}`;

const REWARD_RECIPIENT = process.env
  .NEXT_PUBLIC_REWARD_RECIPIENT as `0x${string}`;

export const useClanker = () => {
  const { ready, authenticated } = usePrivy();
  const account = useAccount();
  const { wallets } = useWallets();
  const { data: walletClient } = useWalletClient(account);
  const client = createPublicClient({ chain: base, transport: http() });

  const clanker = new Clanker({
    // @ts-ignore, TODO: fix this if possible
    publicClient: client,
    wallet: walletClient,
  });

  const handleDeploy = async (
    name: string,
    symbol: string,
    description: string
  ) => {
    if (!ready) {
      throw new Error("Not ready");
    }
    if (!authenticated) {
      throw new Error("Not authenticated");
    }

    const wallet = wallets.find(
      (w) => w.address.toLowerCase() === account.address?.toLowerCase()
    );

    if (!wallet) {
      throw new Error("Wallet not found");
    }

    await wallet.switchChain(base.id);

    const { txHash, waitForTransaction, error } = await clanker.deploy({
      name,
      symbol,
      metadata: {
        description: `${symbol} token - ${description}`,
        socialMediaUrls: [],
        auditUrls: [],
      },
      type: "v4",
      tokenAdmin: account.address as `0x${string}`,
      vanity: false,
      pool: {
        pairedToken: PAIRED_TOKEN,
        tickIfToken0IsClanker: -60000,
        positions: [
          {
            tickLower: -60000,
            tickUpper: -20000,
            positionBps: 8000,
          },
          {
            tickLower: -20000,
            tickUpper: 100000,
            positionBps: 2000,
          },
        ],
      },
      fees: {
        type: "static",
        clankerFee: 0,
        pairedFee: 100,
      },
      rewards: {
        recipients: [
          {
            recipient: account.address as `0x${string}`,
            admin: account.address as `0x${string}`,
            bps: 9_000,
          },
          {
            recipient: REWARD_RECIPIENT,
            admin: REWARD_RECIPIENT,
            bps: 1_000,
          },
        ],
      },
      vault: {
        percentage: 50,
        lockupDuration: 2592000,
        vestingDuration: 2592000,
      },
    });

    if (error) throw error;
    const { address } = await waitForTransaction();
    console.log(
      `Deployed token to ${address} on chain ${base.id}, tx hash: ${txHash}`
    );
    return { address, txHash };
  };

  return { handleDeploy };
};
