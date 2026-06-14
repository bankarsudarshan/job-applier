import logging
from typing import Any
from app.services.browser.base_driver import ATSProvider

logger = logging.getLogger(__name__)

class LinkedInProvider(ATSProvider):
    async def detect(self) -> bool:
        url = self.page.url.lower()
        if "linkedin.com" in url:
            return True
        btn = await self.page.query_selector(".jobs-apply-button")
        return btn is not None

    async def extract_form(self) -> list[dict[str, Any]]:
        fields = []
        # Look for standard dialog fields or inputs
        inputs = await self.page.query_selector_all("input, select, textarea")
        for inp in inputs:
            name = await inp.get_attribute("name") or await inp.get_attribute("id")
            inp_type = await inp.get_attribute("type") or "text"
            inp_id = await inp.get_attribute("id") or ""

            if not name or inp_type in ["hidden", "submit"]:
                continue

            label_text = name
            parent = await inp.evaluate_handle("el => el.closest('.fb-form-element, .jobs-easy-apply-form-section') || el.parentElement")
            if parent:
                text_content = await parent.evaluate("el => el.innerText")
                if text_content:
                    label_text = text_content.split("\n")[0].strip()

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

    async def fill_and_submit(self, fields: list[dict[str, Any]], resume_path: str | None = None) -> bool:
        try:
            for field in fields:
                val = field.get("value")
                sel = field.get("selector")
                f_type = field.get("field_type")

                if not val or not sel:
                    continue

                if f_type == "file":
                    if resume_path:
                        await self.page.set_input_files(sel, resume_path)
                elif f_type == "select":
                    await self.page.select_option(sel, value=val)
                elif f_type in ["checkbox", "radio"]:
                    if str(val).lower() in ["true", "yes", "1"]:
                        await self.page.check(sel)
                else:
                    await self.page.fill(sel, str(val))

            logger.info("LinkedIn Easy Apply form filled successfully (submit bypassed).")
            return True
        except Exception as e:
            logger.error(f"Error filling LinkedIn form: {e}")
            return False
