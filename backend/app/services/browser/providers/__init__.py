import logging
from typing import Type
from playwright.async_api import Page
from app.services.browser.base_driver import ATSProvider
from app.services.browser.providers.greenhouse import GreenhouseProvider
from app.services.browser.providers.lever import LeverProvider
from app.services.browser.providers.workday import WorkdayProvider
from app.services.browser.providers.ashby import AshbyProvider
from app.services.browser.providers.linkedin import LinkedInProvider
from app.services.browser.providers.smartrecruiters import SmartRecruitersProvider

logger = logging.getLogger(__name__)

PROVIDERS = [
    GreenhouseProvider,
    LeverProvider,
    WorkdayProvider,
    AshbyProvider,
    LinkedInProvider,
    SmartRecruitersProvider
]

async def detect_provider(page: Page) -> ATSProvider | None:
    for provider_cls in PROVIDERS:
        try:
            provider = provider_cls(page)
            if await provider.detect():
                logger.info(f"Detected ATS Provider: {provider_cls.__name__}")
                return provider
        except Exception as e:
            logger.error(f"Error executing detect on {provider_cls.__name__}: {e}")
    return None
