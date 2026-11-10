import "server-only";

import { authEnv } from "./env";

const GRAPH_URL = "https://graph.microsoft.com/v1.0";

// appRoleId Entra uses when someone is assigned to the app without a role.
const DEFAULT_ACCESS_ROLE_ID = "00000000-0000-0000-0000-000000000000";

export interface AppAssignment {
  /** Entra object ID: the same value as app.users.entra_object_id. */
  principalId: string;
  displayName: string;
  /** "User" or "Group". */
  principalType: string;
  role: string;
  assignedAt: string;
}

interface ServicePrincipal {
  id: string;
  appRoles: { id: string; value: string | null }[];
}

interface AssignmentPage {
  value: {
    principalId: string;
    principalDisplayName: string;
    principalType: string;
    appRoleId: string;
    createdDateTime: string;
  }[];
  "@odata.nextLink"?: string;
}

/**
 * Token for TAP's own app registration (client credentials). Needs the
 * Application.Read.All application permission, with admin consent.
 */
async function graphToken(): Promise<string> {
  const env = authEnv();
  const response = await fetch(`https://login.microsoftonline.com/${env.tenantId}/oauth2/v2.0/token`, {
    method: "POST",
    body: new URLSearchParams({
      client_id: env.clientId,
      client_secret: env.clientSecret,
      scope: "https://graph.microsoft.com/.default",
      grant_type: "client_credentials",
    }),
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Graph token request failed with status ${response.status}`);
  }
  const body = (await response.json()) as { access_token: string };
  return body.access_token;
}

async function graphGet<T>(token: string, url: string): Promise<T> {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Graph request failed with status ${response.status}: ${await response.text()}`);
  }
  return (await response.json()) as T;
}

/** Users and groups assigned to the TAP enterprise application, with their app role. */
export async function listAppAssignments(): Promise<AppAssignment[]> {
  const token = await graphToken();

  const app = await graphGet<ServicePrincipal>(
    token,
    `${GRAPH_URL}/servicePrincipals(appId='${authEnv().clientId}')?$select=id,appRoles`,
  );
  const roleNames = new Map(app.appRoles.map((r) => [r.id, r.value ?? r.id]));
  roleNames.set(DEFAULT_ACCESS_ROLE_ID, "Default access");

  const assignments: AppAssignment[] = [];
  let url: string | undefined = `${GRAPH_URL}/servicePrincipals/${app.id}/appRoleAssignedTo`;
  while (url) {
    const page: AssignmentPage = await graphGet<AssignmentPage>(token, url);
    for (const a of page.value) {
      assignments.push({
        principalId: a.principalId,
        displayName: a.principalDisplayName,
        principalType: a.principalType,
        role: roleNames.get(a.appRoleId) ?? a.appRoleId,
        assignedAt: a.createdDateTime,
      });
    }
    url = page["@odata.nextLink"];
  }

  return assignments.sort((a, b) => a.displayName.localeCompare(b.displayName));
}
