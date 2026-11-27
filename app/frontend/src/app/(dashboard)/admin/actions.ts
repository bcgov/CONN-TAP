"use server";

import { revalidatePath } from "next/cache";
import { getCurrentSession } from "@/lib/server/auth";
import { setOrganization } from "@/lib/server/user-organizations";

/**
 * Called from the admin page's drop-down: sets the user's one organization.
 * organization is "bge:<id>" or "sub_bge:<id>". Server actions can be called
 * directly, so the role is checked here too, not only on the page.
 */
export async function setOrganizationAction(
  entraObjectId: string,
  displayName: string,
  organization: string,
): Promise<void> {
  const session = await getCurrentSession();
  if (!session || !session.roles.includes("to_admin")) {
    throw new Error("Only TO admins can assign organizations");
  }

  const [kind, idText] = organization.split(":");
  const id = Number(idText);
  if (!Number.isInteger(id) || (kind !== "bge" && kind !== "sub_bge")) {
    throw new Error(`Unknown organization: ${organization}`);
  }

  await setOrganization(
    entraObjectId,
    displayName,
    kind === "bge" ? id : null,
    kind === "sub_bge" ? id : null,
    session.subject,
  );
  revalidatePath("/admin");
}
