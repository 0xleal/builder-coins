import { supabase } from "@/lib/supabase";
import { notFound } from "next/navigation";
import FundDetails from "@/components/fund-details";
import { FundManagerAllocation } from "@/lib/types";

export default async function FundPage() {
  const { data: fundManagerAllocations, error } = await supabase
    .from("fund_strategies")
    .select("*")
    .order("created_at", { ascending: false })
    .single();

  if (error || !fundManagerAllocations) {
    notFound();
  }

  return (
    <FundDetails
      fundManagerAllocations={
        fundManagerAllocations.strategy as FundManagerAllocation[]
      }
    />
  );
}
