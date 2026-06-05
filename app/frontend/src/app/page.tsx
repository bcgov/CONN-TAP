import { redirect } from "next/navigation";
import { HomeClient } from "./home-client";
import { getCurrentSession } from "@/lib/server/auth";

export default async function HomePage() {
  const session = await getCurrentSession();
  if (session) {
    redirect("/dashboard");
  }

  return <HomeClient />;
}
