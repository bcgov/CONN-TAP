import { redirect } from "next/navigation";
import { getCurrentSession } from "@/lib/server/auth";
import { parseChefsFormUrl } from "@/lib/chefs-form-url";
import { HomeClient } from "./home-client";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const session = await getCurrentSession();
  if (session) {
    redirect("/dashboard");
  }

  // Read at request time (not NEXT_PUBLIC_) so the form can change without a rebuild.
  return <HomeClient chefsFormUrl={parseChefsFormUrl(process.env.CHEFS_TEST_FORM_URL)} />;
}
