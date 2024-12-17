import asyncio

from src.browser.browser import Browser


class BrowserPool:
    def __init__(self, size):
        self.size = size
        self.browsers = []
        self.lock = asyncio.Lock()

    async def initialize(self):
        for _ in range(self.size):
            browser = Browser()
            await browser.initialize()
            self.browsers.append(browser)

    async def get_available_browser(self):
        while True:
            async with self.lock:
                for browser in self.browsers:
                    if not browser.is_busy:
                        browser.is_busy = True
                        return browser
            await asyncio.sleep(0.1)

    async def release_browser(self, browser):
        async with self.lock:
            browser.is_busy = False

    async def cleanup(self):
        for browser in self.browsers:
            await browser.cleanup()
