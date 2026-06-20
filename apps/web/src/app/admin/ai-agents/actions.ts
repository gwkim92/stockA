"use server";

import {
  runCodexOauthDirectSmoke,
  runCodexOauthNewsSmoke,
  startCodexOauthRelogin,
} from "@/lib/frontend-api";
import type { CodexOauthOperatorStatus } from "@/lib/types";

export type CodexOauthActionState = {
  ok: boolean;
  message: string;
  status: CodexOauthOperatorStatus | null;
};

function failureMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }
  return "요청 실행 중 알 수 없는 오류가 발생했다.";
}

async function runAction(action: () => Promise<CodexOauthOperatorStatus>): Promise<CodexOauthActionState> {
  try {
    const status = await action();
    return {
      ok: true,
      message: status.next_action || status.summary,
      status,
    };
  } catch (error) {
    return {
      ok: false,
      message: failureMessage(error),
      status: null,
    };
  }
}

export async function startCodexOauthReloginAction(): Promise<CodexOauthActionState> {
  return runAction(startCodexOauthRelogin);
}

export async function runCodexOauthDirectSmokeAction(): Promise<CodexOauthActionState> {
  return runAction(runCodexOauthDirectSmoke);
}

export async function runCodexOauthNewsSmokeAction(): Promise<CodexOauthActionState> {
  return runAction(runCodexOauthNewsSmoke);
}
