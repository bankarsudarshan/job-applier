import logging
from playwright.async_api import Page
from app.services.browser.providers import detect_provider, ATSProvider

logger = logging.getLogger(__name__)

class ATSDetector:
    async def detect_ats(self, page: Page) -> ATSProvider | None:
        provider = await detect_provider(page)
        if provider:
            return provider
        logger.warning(f"No specific ATS provider detected for URL: {page.url}")
        return None

ats_detector = ATSDetector()
