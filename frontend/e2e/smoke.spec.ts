import { test, expect } from "@playwright/test";

/**
 * Smoke tests for Edison UI core functionality.
 * These tests validate basic navigation and page rendering.
 */

test.describe("Edison UI Smoke Tests", () => {
  test("homepage loads and displays dashboard", async ({ page }) => {
    await page.goto("/");

    // Should display the dashboard heading
    await expect(
      page.getByRole("heading", { name: "Dashboard", level: 1 })
    ).toBeVisible();

    // Should have main navigation with Dashboard and Projects links
    const mainNav = page.getByRole("navigation", { name: "Main navigation" });
    await expect(mainNav.getByRole("link", { name: "Dashboard" })).toBeVisible();
    await expect(mainNav.getByRole("link", { name: "Projects" })).toBeVisible();
  });

  test("projects page loads", async ({ page }) => {
    await page.goto("/projects");

    // Should display projects heading
    await expect(
      page.getByRole("heading", { name: "Projects", level: 1 })
    ).toBeVisible();
  });

  test("navigation between pages works", async ({ page }) => {
    await page.goto("/");

    // Click on Projects link in main navigation
    await page
      .getByRole("navigation", { name: "Main navigation" })
      .getByRole("link", { name: "Projects" })
      .click();

    // Should navigate to projects page
    await expect(page).toHaveURL(/\/projects/);

    // Should show Projects heading (wait for page to fully load)
    await expect(
      page.getByRole("heading", { name: "Projects", level: 1 })
    ).toBeVisible({ timeout: 10000 });
  });
});
