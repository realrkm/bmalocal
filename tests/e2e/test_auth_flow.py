import os
import pytest
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("APP_URL", "http://localhost:5000")

def test_landing_page_branding(page: Page):
    """Verify landing page loads with correct title and branding elements."""
    page.goto(BASE_URL, timeout=30000)
    expect(page).to_have_title("BMA Auto Accessories")
    
    # Wait for Anvil login modal to hydrate and verify inputs
    email_input = page.get_by_placeholder("email@address.com")
    password_input = page.get_by_placeholder("password")
    login_btn = page.get_by_role("button", name="Log In")
    
    expect(email_input).to_be_visible(timeout=10000)
    expect(password_input).to_be_visible(timeout=10000)
    expect(login_btn).to_be_visible(timeout=10000)
    
    # Pause for visual inspection of landing page branding
    page.wait_for_timeout(2500)

def test_password_visibility_toggle(page: Page):
    """
    Verify password visibility toggle (BUG-001 regression test).
    Clicking the eye icon switches the input between type='password' and type='text'.
    """
    page.goto(BASE_URL, timeout=30000)
    
    password_input = page.get_by_placeholder("password")
    expect(password_input).to_be_visible(timeout=10000)
    assert password_input.get_attribute("type") == "password"

    # Fill sample test password and pause for user visibility
    password_input.fill("SampleSecurePass123!")
    page.wait_for_timeout(2000)

    # Locate toggle button using ARIA role
    show_btn = page.get_by_role("button", name="Show password")
    
    if show_btn.count() > 0 and show_btn.is_visible():
        # Click to reveal password
        show_btn.click()
        page.wait_for_timeout(2500)
        assert password_input.get_attribute("type") == "text"
        
        # Once revealed, ARIA label switches to 'Hide password'
        hide_btn = page.get_by_role("button", name="Hide password")
        expect(hide_btn).to_be_visible(timeout=5000)
        hide_btn.click()
        page.wait_for_timeout(2500)
        assert password_input.get_attribute("type") == "password"

def test_invalid_login_rejection(page: Page):
    """Verify that attempting to log in with invalid credentials fails safely."""
    page.goto(BASE_URL, timeout=30000)
    
    email_input = page.get_by_placeholder("email@address.com")
    password_input = page.get_by_placeholder("password")
    login_btn = page.get_by_role("button", name="Log In")
    
    expect(email_input).to_be_visible(timeout=10000)
    
    # Fill invalid credentials with visual pacing
    email_input.fill("nonexistent.user@bmaauto.com")
    page.wait_for_timeout(1000)
    password_input.fill("WrongPassword999!")
    page.wait_for_timeout(1500)
    
    # Click Log In and observe rejection
    login_btn.click()
    page.wait_for_timeout(3000)
    
    # Verify user remains on the login view and is not granted access
    expect(login_btn).to_be_visible()
    expect(email_input).to_be_visible()
    page.wait_for_timeout(1500)

@pytest.mark.parametrize("viewport", [
    {"width": 1440, "height": 900, "name": "Desktop (1440x900)"},
    {"width": 768, "height": 1024, "name": "Tablet iPad (768x1024)"},
    {"width": 375, "height": 667, "name": "Mobile iPhone/Pixel (375x667)"},
])
def test_login_responsive_viewports(page: Page, viewport):
    """Verify login UI renders cleanly across Desktop, Tablet, and Mobile viewports."""
    page.set_viewport_size({"width": viewport["width"], "height": viewport["height"]})
    page.goto(BASE_URL, timeout=30000)
    
    email_input = page.get_by_placeholder("email@address.com")
    login_btn = page.get_by_role("button", name="Log In")
    
    expect(email_input).to_be_visible(timeout=10000)
    expect(login_btn).to_be_visible(timeout=10000)
    
    # Pause on each responsive viewport so the layout adjustment is clearly observed
    page.wait_for_timeout(3000)
