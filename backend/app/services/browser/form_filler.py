import logging
from typing import Any
from playwright.async_api import Page
from app.services.browser.base_driver import ATSProvider

logger = logging.getLogger(__name__)

class FormFiller:
    async def fill(self, page: Page, fields: list[dict[str, Any]], resume_path: str | None = None, provider: ATSProvider | None = None) -> bool:
        if provider:
            logger.info("Filling form using detected ATS provider...")
            return await provider.fill_and_submit(fields, resume_path)

        logger.info("Filling form using generic fallback filler...")
        try:
            for field in fields:
                val = field.get("value")
                sel = field.get("selector")
                f_type = field.get("field_type")

                if not val or not sel:
                    continue

                if f_type == "file":
                    if resume_path:
                        await page.set_input_files(sel, resume_path)
                elif f_type == "select":
                    await page.select_option(sel, value=val)
                elif f_type in ["checkbox", "radio"]:
                    if str(val).lower() in ["true", "yes", "1"]:
                        await page.check(sel)
                else:
                    await page.fill(sel, str(val))

            logger.info("Generic form filled successfully.")
            return True
        except Exception as e:
            logger.error(f"Error in generic form filler: {e}")
            return False

form_filler = FormFiller()
