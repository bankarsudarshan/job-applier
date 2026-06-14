import logging
from typing import Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

logger = logging.getLogger(__name__)

class BaseDriver:
    def __init__(self) -> None:
        self.playwright = None
        self.browser: Browser | None = None

    async def start(self, headless: bool = True) -> None:
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            logger.info("Playwright browser launched successfully.")
        except Exception as e:
            logger.error(f"Failed to launch Playwright browser: {e}")
            raise e

    async def stop(self) -> None:
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser stopped.")

    async def get_page(self) -> Page:
        if not self.browser:
            await self.start()
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        return page

class ATSProvider:
    def __init__(self, page: Page) -> None:
        self.page = page

    async def detect(self) -> bool:
        """Returns True if this provider is active on the current page."""
        raise NotImplementedError

    async def extract_form(self) -> list[dict[str, Any]]:
        """Extracts input fields from the current page."""
        raise NotImplementedError

    async def fill_and_submit(self, fields: list[dict[str, Any]], resume_path: str | None = None) -> bool:
        """Fills the form fields and clicks submit."""
        raise NotImplementedError
