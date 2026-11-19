import { redirect } from "next/navigation";
import { getCurrentSession } from "@/lib/server/auth";
import { HomeClient } from "./home-client";

export const dynamic = "force-dynamic";

// Messages for the `authError` values set by /auth/callback.
const AUTH_ERROR_MESSAGES: Record<string, string> = {
  access_denied:
    "Sign-in was cancelled, or you don't have access to TAP. If you need access, contact the Telecom Office.",
};
const DEFAULT_AUTH_ERROR_MESSAGE =
  "Sign-in didn't work. Please try again. If it keeps happening, contact the Telecom Office.";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ authError?: string }>;
}) {
  const session = await getCurrentSession();
  if (session) {
    redirect("/dashboard");
  }

  const { authError } = await searchParams;
  const authErrorMessage = authError
    ? (AUTH_ERROR_MESSAGES[authError] ?? DEFAULT_AUTH_ERROR_MESSAGE)
    : undefined;

  return <HomeClient authErrorMessage={authErrorMessage} />;
}
