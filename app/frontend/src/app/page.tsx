import { redirect } from "next/navigation";
import { getCurrentSession } from "@/lib/server/auth";
import { HomeClient } from "./home-client";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const session = await getCurrentSession();
  if (session) {
    redirect("/dashboard");
  }

  return <HomeClient />;
}
