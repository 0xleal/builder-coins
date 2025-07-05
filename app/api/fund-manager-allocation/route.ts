import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";
import { Database } from "@/lib/database-types";
import { FundManagerAllocation } from "@/lib/types";

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_KEY;
const BACKEND_API_KEY = process.env.BACKEND_API_KEY;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  throw new Error(
    "Missing required environment variables: SUPABASE_URL or SUPABASE_KEY"
  );
}

if (!BACKEND_API_KEY) {
  throw new Error("Missing required environment variables: BACKEND_API_KEY");
}

const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_KEY);

export async function POST(req: NextRequest) {
  const headers = req.headers;
  const authHeader = headers.get("x-api-key");
  if (!authHeader) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (authHeader !== BACKEND_API_KEY) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    // Parse request body
    let body: unknown;
    try {
      body = await req.json();
    } catch (error) {
      return NextResponse.json(
        { error: "Invalid JSON in request body" },
        { status: 400 }
      );
    }

    const data = body as FundManagerAllocation[];

    // Insert into database
    const { data: insertedData, error } = await supabase
      .from("fund_strategies")
      .insert({
        strategy: data,
      })
      .select();

    if (error) {
      console.error("Database insert error:", error);
      return NextResponse.json(
        { error: "Failed to save fund strategy" },
        { status: 500 }
      );
    }

    // Success response
    return NextResponse.json({
      message: "Fund manager allocation saved successfully",
      strategy_id: insertedData[0]?.id,
      total_allocations: data.length,
      total_percentage: data.reduce(
        (sum, item) => sum + item.allocation_percentage,
        0
      ),
      created_at: insertedData[0]?.created_at,
    });
  } catch (error) {
    console.error("Unexpected error in fund-manager-allocation:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
