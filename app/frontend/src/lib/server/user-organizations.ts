import "server-only";

import { query } from "./db";

/** One entry in the "assign organization" drop-down. value is "bge:<id>" or "sub_bge:<id>". */
export interface OrganizationOption {
  value: string;
  label: string;
}

/** What TAP knows about a user, keyed by their Entra object ID. */
export interface TapUser {
  lastLoginAt: string | null;
  /** The assigned organization as a drop-down value ("bge:<id>" / "sub_bge:<id>"), or null. */
  organization: string | null;
}

interface BgeRow {
  id: number;
  name: string;
}

interface SubBgeRow {
  id: number;
  name: string;
  bge_id: number;
  parent_sub_bge_id: number | null;
}

/**
 * Every BGE, each followed by its sub-BGEs / service designees in hierarchy
 * order. Each level down is prefixed with one more "— ".
 */
export async function listOrganizationOptions(): Promise<OrganizationOption[]> {
  const bges = (await query<BgeRow>("SELECT id, name FROM reference_data.bge ORDER BY name")).rows;
  const subBges = (
    await query<SubBgeRow>(
      "SELECT id, name, bge_id, parent_sub_bge_id FROM reference_data.sub_bge ORDER BY name",
    )
  ).rows;

  const options: OrganizationOption[] = [];

  function addChildren(bgeId: number, parentId: number | null, depth: number) {
    for (const sub of subBges) {
      if (sub.bge_id === bgeId && sub.parent_sub_bge_id === parentId) {
        options.push({ value: `sub_bge:${sub.id}`, label: `${"— ".repeat(depth)}${sub.name}` });
        addChildren(bgeId, sub.id, depth + 1);
      }
    }
  }

  for (const bge of bges) {
    options.push({ value: `bge:${bge.id}`, label: bge.name });
    addChildren(bge.id, null, 1);
  }
  return options;
}

/**
 * TAP user rows and their assigned organization, for the given Entra object IDs.
 * For now each user has one organization (the admin page replaces it); if a
 * user still has several rows, the newest one is shown.
 */
export async function listTapUsers(entraObjectIds: string[]): Promise<Map<string, TapUser>> {
  const result = await query<{ entra_object_id: string; last_login_at: Date | null; organization: string | null }>(
    `SELECT DISTINCT ON (u.id)
            u.entra_object_id,
            u.last_login_at,
            coalesce('bge:' || uo.bge_id, 'sub_bge:' || uo.sub_bge_id) AS organization
       FROM users u
       LEFT JOIN user_organizations uo ON uo.user_id = u.id
      WHERE u.entra_object_id = ANY($1)
      ORDER BY u.id, uo.created_at DESC`,
    [entraObjectIds],
  );

  const users = new Map<string, TapUser>();
  for (const row of result.rows) {
    users.set(row.entra_object_id, {
      lastLoginAt: row.last_login_at?.toISOString() ?? null,
      organization: row.organization,
    });
  }
  return users;
}

/**
 * Set a user's organization (a BGE or sub-BGE), replacing any other they had.
 * Creates the TAP user row first if they haven't signed in yet; sign-in
 * matches it by entra_object_id later.
 */
export async function setOrganization(
  entraObjectId: string,
  displayName: string,
  bgeId: number | null,
  subBgeId: number | null,
  assignedByEntraObjectId: string,
): Promise<void> {
  await query(
    `INSERT INTO users (entra_object_id, display_name)
     VALUES ($1, $2)
     ON CONFLICT (entra_object_id) DO NOTHING`,
    [entraObjectId, displayName],
  );

  // One statement, so the old organization is removed and the new one added
  // together. The new organization's row is kept if it already exists.
  await query(
    `WITH target_user AS (
         SELECT id FROM users WHERE entra_object_id = $1
     ),
     removed AS (
         DELETE FROM user_organizations uo
          USING target_user t
          WHERE uo.user_id = t.id
            AND (uo.bge_id IS DISTINCT FROM $2::integer OR uo.sub_bge_id IS DISTINCT FROM $3::integer)
     )
     INSERT INTO user_organizations (user_id, bge_id, sub_bge_id, assigned_by)
     SELECT t.id, $2::integer, $3::integer, (SELECT id FROM users WHERE entra_object_id = $4)
       FROM target_user t
     ON CONFLICT DO NOTHING`,
    [entraObjectId, bgeId, subBgeId, assignedByEntraObjectId],
  );
}
