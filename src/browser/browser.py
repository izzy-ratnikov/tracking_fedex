import asyncio
import random
from playwright.async_api import async_playwright

from src.config.profiles import browser_profiles
from src.config.proxies import proxy_server, proxy_password


class Browser:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None
        self.page = None
        self.lock = asyncio.Lock()
        self.is_busy = False
        self.initialized_with_tracking = False
        self.request_details = None
        self.profile = random.choice(list(browser_profiles.values()))

    async def reinitialize(self):
        """Fully reinitialize the browser and all its components"""
        try:
            await self.cleanup()
            await self.initialize()
            self.initialized_with_tracking = False
            self.request_details = None
        except Exception as e:
            print(f"Error during browser reinitialization: {e}")

    async def initialize(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                f'--user-agent={self.profile["user_agent"]}'
            ]
        )
        await self.create_context()

    async def create_context(self):

        country_codes = [
            "us",  # United States
            "in",  # India
            "jp",  # Japan
            "de",  # Germany
            "br",  # Brazil
            "fr",  # France
            "gb",  # United Kingdom
            "ca",  # Canada
            "au",  # Australia
            "kr",  # South Korea
            "mx",  # Mexico
            "es",  # Spain
            "it",  # Italy
            "tr",  # Turkey
            "pl",  # Poland
            "nl",  # Netherlands
            "ar",  # Argentina
            "ch",  # Switzerland
            "za",  # South Africa
            "se",  # Sweden
            "be",  # Belgium
            "pt",  # Portugal
            "hu",  # Hungary
            "cz",  # Czech Republic
            "ro",  # Romania
            "my",  # Malaysia
            "th",  # Thailand
            "ph",  # Philippines
            "sk",  # Slovakia
            "lt",  # Lithuania
            "is",  # Iceland
        ]
        country_code = random.choice(country_codes)
        self.context = await self.browser.new_context(
            proxy={
                "server": proxy_server,
                "username": f'pool-nflx_{country_code}-session-{random.randint(100000, 999999)}',
                "password": proxy_password
            },
            user_agent=self.profile["user_agent"],
            extra_http_headers={
                'sec-ch-ua': self.profile["sec_ch_ua"],
                'sec-ch-ua-mobile': self.profile["sec_ch_ua_mobile"],
                'sec-ch-ua-platform': self.profile["sec_ch_ua_platform"]
            }
        )
        self.page = await self.context.new_page()
        await self.setup_page(self.page)

    async def setup_page(self, page):
        async def handle_route(route):
            blocked_substrings = [
                "clientlib-dependencies",
                "simplifiedhf",
                "track/scripts",
                "com/akam/",
                ".digital.nuance.com",
                "com/assets/"
            ]
            if (route.request.resource_type in ['stylesheet', 'font', 'image'] or
                    any(substring in route.request.url for substring in blocked_substrings)):
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", handle_route)

    async def cleanup(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
