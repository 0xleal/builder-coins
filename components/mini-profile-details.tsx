import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { FundManagerAllocation } from "@/lib/types";
import { mainnet } from "viem/chains";
import { useEnsAvatar, useEnsName } from "wagmi";

export function MiniProfileDetails({
  allocation,
}: {
  allocation: FundManagerAllocation;
}) {
  const { data: ensName } = useEnsName({
    address: allocation.deployer_address as `0x${string}`,
    chainId: mainnet.id,
  });
  const { data: ensAvatar } = useEnsAvatar({
    name: ensName as string,
    chainId: mainnet.id,
  });

  return (
    <>
      <Avatar>
        <AvatarImage src={ensAvatar as string} alt={ensName as string} />
        <AvatarFallback className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
          {ensName || allocation.token_address.slice(2, 4).toUpperCase()}
        </AvatarFallback>
      </Avatar>
      <div>
        <div className="flex items-center space-x-2">
          <h3 className="text-white font-semibold">
            {ensName
              ? ensName
              : allocation.token_address.slice(0, 6) +
                "..." +
                allocation.token_address.slice(-4)}
          </h3>
          <Badge variant="secondary" className="bg-white/10 text-white/80">
            Token
          </Badge>
        </div>
        <p className="text-white/60 text-sm">
          Builder Score: {allocation.builder_score}
        </p>
      </div>
    </>
  );
}
