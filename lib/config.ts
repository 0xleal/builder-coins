import { createConfig } from "@privy-io/wagmi";
import { baseSepolia } from "viem/chains";
import { http } from "wagmi";

export const config = createConfig({
  chains: [baseSepolia],
  transports: {
    [baseSepolia.id]: http(),
  },
});

declare module "wagmi" {
  interface Register {
    config: typeof config;
  }
}
