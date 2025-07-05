import BuilderDetails from "@/components/builder-details";
import { supabase } from "@/lib/supabase";
import { notFound } from "next/navigation";
import { mapTokenDataToBuilder } from "@/lib/utils";
import { Builder } from "@/lib/types";
import { MOCK_DATA } from "@/lib/mock-data";

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

  // Transform the database response to match the Builder type
  const mappedTokenData = mapTokenDataToBuilder(tokenData);

  const builder: Builder = {
    ...MOCK_DATA,
    ...mappedTokenData,
  };

  return <BuilderDetails builder={builder} />;
}
