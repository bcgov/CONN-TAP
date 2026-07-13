import { test, expect } from "@playwright/test";

test("home page renders welcome content for unauthenticated visitors", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: /welcome to the telecom access point/i }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: /login with idir/i })).toBeVisible();
});
