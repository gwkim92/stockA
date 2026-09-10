import { NextRequest } from "next/server";
import { proxyModelSettings } from "@/lib/model-settings-proxy";

export const dynamic = "force-dynamic";
export const POST = (request: NextRequest) => proxyModelSettings(request, true);
export const DELETE = (request: NextRequest) => proxyModelSettings(request, true);
