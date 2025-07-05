"use client";

import { useLogin, usePrivy } from "@privy-io/react-auth";
import { useState } from "react";
import { useAccount, useDisconnect } from "wagmi";
import { Button } from "./ui/button";

export default function Login() {
  const [isLoading, setIsLoading] = useState(false);
  const { login } = useLogin({});
  const { logout } = usePrivy();
  const { address } = useAccount();
  const { disconnectAsync } = useDisconnect();

  const handleLogin = async () => {
    setIsLoading(true);
    await login();
    setIsLoading(false);
  };

  const handleLogout = async () => {
    setIsLoading(true);
    await disconnectAsync();
    await logout();
    setIsLoading(false);
  };

  if (!address) {
    return (
      <Button
        variant="outline"
        className="border-white/20 text-white hover:bg-white/10 bg-transparent"
        onClick={handleLogin}
        disabled={isLoading}
      >
        {isLoading ? "Loading..." : "Login"}
      </Button>
    );
  }

  return (
    <>
      <Button
        variant="outline"
        className="border-white/20 text-white hover:bg-white/10 bg-transparent"
        onClick={handleLogout}
        disabled={isLoading}
      >
        {isLoading
          ? "Loading..."
          : address.slice(0, 6) + "..." + address.slice(-4)}
      </Button>
    </>
  );
}
