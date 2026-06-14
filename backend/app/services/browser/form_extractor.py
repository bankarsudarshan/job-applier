import logging
from typing import Any
from playwright.async_api import Page
from app.services.browser.base_driver import ATSProvider

logger = logging.getLogger(__name__)

class FormExtractor:
    async def extract(self, page: Page, provider: ATSProvider | None = None) -> list[dict[str, Any]]:
        if provider:
            logger.info("Extracting form using detected ATS provider...")
            return await provider.extract_form()

        logger.info("Extracting form using generic fallback extractor...")
        fields = []
        inputs = await page.query_selector_all("input, select, textarea")
        for inp in inputs:
            name = await inp.get_attribute("name")
            inp_id = await inp.get_attribute("id") or ""
            inp_type = await inp.get_attribute("type") or "text"

            if not name or inp_type in ["hidden", "submit"]:
                continue

            # Look for generic label
            label_text = name
            if inp_id:
                label_el = await page.query_selector(f"label[for='{inp_id}']")
                if label_el:
                    label_text = await label_el.inner_text()

            is_required = await inp.get_attribute("required") is not None
            
            options = []
            if inp_type == "select" or await inp.evaluate("el => el.tagName.toLowerCase() == 'select'"):
                inp_type = "select"
                option_els = await inp.query_selector_all("option")
                for opt in option_els:
                    opt_val = await opt.get_attribute("value")
                    opt_text = await opt.inner_text()
                    if opt_val:
                        options.append({"value": opt_val, "label": opt_text.strip()})

            fields.append({
                "field_name": label_text.strip().replace("*", "").strip(),
                "normalized_key": name,
                "field_type": inp_type,
                "options": options,
                "is_required": is_required,
                "selector": f"[name='{name}']" if name else f"#{inp_id}"
            })
        return fields

form_extractor = FormExtractor()
