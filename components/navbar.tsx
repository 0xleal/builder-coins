"use client";

import Link from "next/link";
import Login from "./login";

export function Navbar() {
  return (
    <nav className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500" />
            <span className="text-xl font-bold text-white">BuildersFund</span>
          </div>
          <div className="flex items-center space-x-6">
            <Link
              href="/fund"
              className="text-white/80 hover:text-white transition-colors"
            >
              Fund
            </Link>
            <Link
              href="/builder"
              className="text-white/80 hover:text-white transition-colors"
            >
              Launch Token
            </Link>
            <Login />
          </div>
        </div>
      </div>
    </nav>
  );
}
