import { NextRequest } from "next/server";
import { proxyModelSettings } from "@/lib/model-settings-proxy";

export const dynamic = "force-dynamic";
export const GET = (request: NextRequest) => proxyModelSettings(request);
export const PATCH = (request: NextRequest) => proxyModelSettings(request);
