import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { Builder } from "./types";
import { Database } from "./database-types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Function to convert snake_case to camelCase
export function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase());
}

// Type to convert snake_case string to camelCase
type CamelCase<S extends string> = S extends `${infer P1}_${infer P2}`
  ? `${P1}${Capitalize<CamelCase<P2>>}`
  : S;

// Type to recursively convert object keys from snake_case to camelCase
type KeysToCamelCase<T> = T extends Record<string, unknown>
  ? {
      [K in keyof T as CamelCase<string & K>]: T[K] extends Record<
        string,
        unknown
      >
        ? KeysToCamelCase<T[K]>
        : T[K] extends (infer U)[]
        ? U extends Record<string, unknown>
          ? KeysToCamelCase<U>[]
          : T[K]
        : T[K];
    }
  : T;

// Function to convert object keys from snake_case to camelCase
export function convertKeysToCamelCase<T>(obj: T): KeysToCamelCase<T> {
  if (obj === null || typeof obj !== "object") {
    return obj as KeysToCamelCase<T>;
  }

  if (Array.isArray(obj)) {
    return obj.map(convertKeysToCamelCase) as KeysToCamelCase<T>;
  }

  const converted = {} as Record<string, unknown>;
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = toCamelCase(key);
    converted[camelKey] = convertKeysToCamelCase(value);
  }

  return converted as KeysToCamelCase<T>;
}

type TokenDeployment = Database["public"]["Tables"]["token_deployments"]["Row"];

// Function to map database response to Builder type
export function mapTokenDataToBuilder(
  tokenData: TokenDeployment
): Partial<Builder> {
  const camelCaseData = convertKeysToCamelCase(tokenData);

  return {
    tokenAddress: camelCaseData.tokenAddress,
    adminAddress: camelCaseData.adminAddress,
    tokenName: camelCaseData.tokenName,
    tokenSymbol: camelCaseData.tokenSymbol,
    deployerAddress: camelCaseData.deployerAddress,
    pairedToken: camelCaseData.pairedToken,
    tokenMetadata: camelCaseData.tokenMetadata as
      | Builder["tokenMetadata"]
      | undefined,
    blockNumber: camelCaseData.deploymentBlockNumber,
    profileImage: camelCaseData.tokenImage ?? undefined,
    profileName: camelCaseData.tokenName, // Using token name as profile name
  };
}
