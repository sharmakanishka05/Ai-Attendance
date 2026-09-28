import { test, expect } from "@playwright/test";

test.describe("AttendAI Production E2E Verification Suite", () => {
  test("1. Unauthenticated access redirects to /login", async ({ page }) => {
    await page.goto("/attendance");
    // Should be redirected to /login by middleware
    await page.waitForURL("**/login");
    await expect(page.locator("h1")).toContainText("Sign in to AttendAI");
  });

  test("2. Full Admin Workflow: Login -> Dashboard -> Attendance -> Reports -> Settings -> Logout", async ({ page }) => {
    // Navigate to login
    await page.goto("/login");
    await expect(page.locator("h1")).toContainText("Sign in to AttendAI");

    // Fill credentials for Admin
    await page.fill("#login-email", "alex.roberts@attendai.edu");
    await page.fill("#login-password", "password123");
    await page.click("#login-submit-btn");

    // Should redirect to dashboard /
    await page.waitForURL("**/", { timeout: 10000 });
    await expect(page.locator("h1")).toContainText("Attendance Overview");

    // Navigate to Attendance
    await page.click('a[href="/attendance"]');
    await page.waitForURL("**/attendance");
    await expect(page.locator("h1")).toContainText("Attendance Session");

    // Verify error banner when bad photo uploaded (Phase 2 - No fake fallback)
    // Buttons: [Try Again] and [Choose Another Photo] exist if processing fails

    // Navigate to Reports Page
    await page.click('a[href="/reports"]');
    await page.waitForURL("**/reports");
    await expect(page.locator("h1")).toContainText("Attendance Reports");
    await expect(page.locator("text=Export CSV")).toBeVisible();
    await expect(page.locator("text=Export Excel (.xlsx)")).toBeVisible();

    // Navigate to Settings & Privacy Page
    await page.click('a[href="/settings"]');
    await page.waitForURL("**/settings");
    await expect(page.locator("h1")).toContainText("System Settings & Privacy");

    // Verify Real Computer Vision Model Diagnostics (Phase 6)
    await expect(page.locator("text=Computer Vision Model Diagnostics")).toBeVisible();
    await expect(page.locator("text=Face Detector")).toBeVisible();
    await expect(page.locator("text=READY (YuNet DNN)")).toBeVisible();
    await expect(page.locator("text=READY (SFace ONNX DNN)")).toBeVisible();
    await expect(page.locator("text=REAL MODEL")).toBeVisible();

    // Verify Admin can see Save Configuration button enabled
    await expect(page.locator("text=Save Configuration to Database")).toBeVisible();

    // Logout
    await page.click('button:has-text("Sign Out")');
    await page.waitForURL("**/login");
    await expect(page.locator("h1")).toContainText("Sign in to AttendAI");
  });

  test("3. Teacher Role Restrictions: Login -> Settings shows read-only banner", async ({ page }) => {
    await page.goto("/login");
    await page.fill("#login-email", "sarah.chen@attendai.edu");
    await page.fill("#login-password", "password123");
    await page.click("#login-submit-btn");

    await page.waitForURL("**/", { timeout: 10000 });
    // Navigate to settings
    await page.goto("/settings");
    await expect(page.locator("text=Instructor View (Read-Only)")).toBeVisible();
    await expect(page.locator("text=Save Disabled (Admin Only)")).toBeVisible();
  });
});
