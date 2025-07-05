import BuilderDetails from "@/components/builder-details";
import { supabase } from "@/lib/supabase";
import { notFound } from "next/navigation";
import { mapTokenDataToBuilder } from "@/lib/utils";
import { Builder, DexscreenerResponse } from "@/lib/types";
import { MOCK_DATA } from "@/lib/mock-data";
import { DEXSCREENER_BASE_URL } from "@/lib/constants";

export default async function BuilderProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const { data: tokenData, error } = await supabase
    .from("token_deployments")
    .select("*")
    .eq("token_address", id)
    .single();

  if (error || !tokenData) {
    notFound();
  }

  let dexscreenerData: DexscreenerResponse | null = null;

  try {
    const response = await fetch(
      `${DEXSCREENER_BASE_URL}/${tokenData.pool_id}`,
      {
        headers: {
          "Content-Type": "application/json",
          Accept: "*/*",
        },
      }
    );

    dexscreenerData = await response.json();
  } catch (error) {
    console.error(error);
  }

  // Transform the database response to match the Builder type
  const mappedTokenData = mapTokenDataToBuilder(tokenData, dexscreenerData);

  const builder: Builder = {
    ...MOCK_DATA,
    ...mappedTokenData,
  };

  return <BuilderDetails builder={builder} />;
}
