import { createConfig } from "@privy-io/wagmi";
import { base, mainnet } from "viem/chains";
import { http } from "wagmi";

export const config = createConfig({
  chains: [base, mainnet],
  transports: {
    [base.id]: http(),
    [mainnet.id]: http(),
  },
});

declare module "wagmi" {
  interface Register {
    config: typeof config;
  }
}
