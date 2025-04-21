import asyncio
from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import json
mcp = FastMCP("PlaywrightTools")

import logging
logging.getLogger("mcp.server").setLevel(logging.WARNING)

class PlaywrightManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None
        self.console_logs: List[Dict] = []
        self.network_requests: List[Dict] = []
        self.initialized = False

    async def init_browser(self, headless: bool = True):
        if self.initialized:
            return

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.initialized = True

    async def close(self):
        if self.page:
            await self.page.close()
            self.page = None
        if self.browser:
            await self.browser.close()
            self.browser = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        self.console_logs.clear()
        self.network_requests.clear()
        self.initialized = False

    async def open_page(self, url: str, headless: bool = True) -> str:
        await self.init_browser(headless)

        if self.page and self.page.url == url:
            return f"Page reused: {url}"

        if self.page:
            await self.page.close()

        self.console_logs.clear()
        self.network_requests.clear()

        self.page = await self.browser.new_page()
        self.page.on("console", self._on_console)
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)

        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        return f"Page opened: {url}"

    def _on_console(self, msg):
        self.console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "location": msg.location,
        })

    def _on_request(self, req):
        self.network_requests.append({
            "url": req.url,
            "method": req.method,
            "headers": req.headers,
            "resourceType": req.resource_type,
        })

    def _on_response(self, res):
        for req in self.network_requests:
            if req["url"] == res.url and "response" not in req:
                req["response"] = {
                    "status": res.status,
                    "statusText": res.status_text,
                    "headers": res.headers,
                }
                break

    async def get_console_logs(self, last_n: int = 10) -> List[Dict]:
        return self.console_logs[-last_n:]

    async def get_network_requests(self, last_n: int = 10) -> List[Dict]:
        return self.network_requests[-last_n:]

    async def get_page_title(self, url: str, headless: bool = False) -> str:
        await self.open_page(url, headless=headless)
        return await self.page.title()

    async def click_and_extract(self, url: str, selector: str, extraction_target: str = "", headless: bool = False) -> str:
        await self.open_page(url, headless=headless)

        if selector.startswith("text="):
            selector = selector.replace("text=", "").strip()

        try:
            # Try clicking on visible text selector
            if " " in selector or selector.isalpha():
                await self.page.get_by_text(selector).wait_for(timeout=10000)
                await self.page.get_by_text(selector).click(timeout=5000)
            else:
                await self.page.click(selector)
            await self.page.wait_for_timeout(2000)
        except Exception as e:
            return f"[Error] Click failed: {str(e)}"

        try:
            # === Dynamic extraction based on intent ===
            extraction_target = extraction_target.lower()
            if "car name" in extraction_target:
                elements = await self.page.locator("div[class*=carInfo] h2, .carInfo h2").all_text_contents()
            elif "spec" in extraction_target:
                elements = await self.page.locator("div[class*=carInfo] ul li").all_text_contents()
            elif "brand" in extraction_target or "manufacturer" in extraction_target:
                elements = await self.page.locator("section:has-text('Explore All Cars') li").all_text_contents()
            else:
                return await self.page.content()  # fallback to raw HTML

            return json.dumps({"extracted": elements})
        except Exception as e:
            return f"[Error] DOM extract failed: {str(e)}"

# === Instantiate and expose MCP tools ===

browser = PlaywrightManager()

@mcp.tool()
async def open_page_and_get_title(url: str, headless: bool = False) -> str:
    return await browser.get_page_title(url, headless=headless)

@mcp.tool()
async def click_element_and_get_text(url: str, selector: str, extraction_target: str = "", headless: bool = False) -> str:
    return await browser.click_and_extract(url, selector, extraction_target, headless=headless)

@mcp.tool()
async def get_console_logs(last_n: int = 10) -> List[Dict]:
    return await browser.get_console_logs(last_n)

@mcp.tool()
async def get_network_requests(last_n: int = 10) -> List[Dict]:
    return await browser.get_network_requests(last_n)

@mcp.tool()
async def close_browser() -> str:
    await browser.close()
    return "Browser closed successfully"

if __name__ == "__main__":
    asyncio.run(mcp.run(transport="stdio"))
