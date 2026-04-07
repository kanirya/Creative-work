import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';
const TEST_EMAIL = process.env.TEST_EMAIL || 'test@iqra.edu.pk';
const TEST_PASSWORD = process.env.TEST_PASSWORD || 'TestPassword123!';

test.describe('EduPilot Web App E2E', () => {
  test('login → dashboard → submit query → verify response', async ({ page }) => {
    // ── Step 1: Navigate to login ──────────────────────────────────────────
    await page.goto(`${BASE_URL}/login`);
    await expect(page).toHaveTitle(/EduPilot/);
    await expect(page.getByRole('heading', { name: 'EduPilot' })).toBeVisible();

    // ── Step 2: Fill login form ────────────────────────────────────────────
    await page.getByLabel('Email Address').fill(TEST_EMAIL);
    await page.getByLabel('Password').fill(TEST_PASSWORD);
    await page.getByRole('button', { name: /sign in/i }).click();

    // ── Step 3: Verify dashboard ───────────────────────────────────────────
    await page.waitForURL(`${BASE_URL}/dashboard`, { timeout: 10_000 });
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();

    // ── Step 4: Navigate to query page ────────────────────────────────────
    await page.getByRole('link', { name: /ask ai/i }).click();
    await page.waitForURL(`${BASE_URL}/query`);
    await expect(page.getByRole('heading', { name: 'Ask AI' })).toBeVisible();

    // ── Step 5: Submit a query ────────────────────────────────────────────
    await page.getByLabel('Your Question').fill('What courses am I enrolled in?');
    await page.getByRole('button', { name: /submit/i }).click();

    // ── Step 6: Verify response appears ───────────────────────────────────
    await expect(page.getByRole('heading', { name: 'Response' })).toBeVisible({ timeout: 15_000 });
    const responseText = page.locator('[aria-live="polite"]');
    await expect(responseText).not.toBeEmpty();
  });

  test('login page shows validation errors for invalid input', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Submit with invalid email
    await page.getByLabel('Email Address').fill('not-an-email');
    await page.getByLabel('Password').fill('password');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByRole('alert')).toContainText(/valid email/i);
  });

  test('unauthenticated user is redirected to login', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForURL(`${BASE_URL}/login`);
    await expect(page.getByRole('heading', { name: 'EduPilot' })).toBeVisible();
  });
});
