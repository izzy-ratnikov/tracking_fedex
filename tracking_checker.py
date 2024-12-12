import asyncio
import math
import os
import json
import random
import time
from playwright.async_api import async_playwright

proxy_server = "http://proxy-us.cravenet.com:7070"
proxy_password = '5efecb83-8e4b-46c1-8aea-a44514f23056'

total_cumulative_request_size = 0
total_cumulative_response_size = 0

browser_profiles = {
    'chrome_windows': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    }, 'chrome_windows_1': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="130", "Chromium";v="130", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'chrome_windows_2': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'chrome_windows_3': {
        'user_agent': 'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'chrome_windows_4': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="129", "Chromium";v="129", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'chrome_windows_5': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="128", "Chromium";v="128", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'chrome_windows_6': {
        'user_agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'chrome_windows_7': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="127", "Chromium";v="127", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'chrome_mac': {
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"macOS"'
    },
    'brave_windows': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'brave_mac': {
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'sec_ch_ua': '"Brave";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"macOS"'
    },
    'firefox_windows': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
        'sec_ch_ua': '"Firefox";v="123", "Not_A Brand";v="24", "Gecko";v="20100101"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'edge_windows': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        'sec_ch_ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    },
    'safari_mac': {
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'sec_ch_ua': '"Safari";v="17", "Apple WebKit";v="605.1.15", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"macOS"'
    },
    'opera_windows': {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/116.0.0.0',
        'sec_ch_ua': '"Opera";v="116", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec_ch_ua_mobile': '?0',
        'sec_ch_ua_platform': '"Windows"'
    }
}


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


async def fetch_content(browser, numbers, retries=3):
    global total_cumulative_request_size, total_cumulative_response_size

    for attempt in range(retries):
        try:
            # If not initialized or no request details, do initial workflow
            if not browser.initialized_with_tracking or not browser.request_details:
                try:
                    page = browser.page
                    # Use all numbers for initialization
                    number_list = ','.join(map(str, numbers))
                    url = f'https://www.fedex.com/fedextrack/summary?trknbr={number_list}'
                    print(f"Initializing browser {id(browser)} with tracking page...")

                    shipment_resp_promise = asyncio.Future()
                    request_details_promise = asyncio.Future()

                    async def handle_request(request):
                        if "api.fedex.com/track/v2/shipments" in request.url:
                            try:
                                headers = dict(request.headers)
                                if not request_details_promise.done():
                                    browser.request_details = {
                                        'headers': headers,
                                        'url': request.url,
                                        'method': request.method,
                                    }
                                    request_details_promise.set_result(True)
                            except Exception as e:
                                print(f"Error capturing request details: {e}")

                    async def handle_shipment_response(response):
                        if "api.fedex.com/track/v2/shipments" in response.url:
                            if response.status == 200:
                                try:
                                    json_data = await response.json()
                                    if not shipment_resp_promise.done():
                                        shipment_resp_promise.set_result(json_data)
                                except Exception as json_error:
                                    print(f"JSON parsing error: {json_error}")

                    page.on("request", handle_request)
                    page.on("response", handle_shipment_response)
                    await page.goto(url)

                    try:
                        # Wait for both promises
                        initial_data, _ = await asyncio.wait_for(asyncio.gather(
                            shipment_resp_promise,
                            request_details_promise
                        ), timeout=30)

                        browser.initialized_with_tracking = True
                        print(f"Browser {id(browser)} successfully initialized with tracking page")

                        # Process the initial data immediately
                        packages = initial_data.get("output", {}).get("packages", [])
                        valid_packages = [pkg for pkg in packages if 'errorList' not in pkg]
                        valid_data = []

                        for pkg in valid_packages:
                            tracking_number = pkg.get('trackingNbr', "")
                            shipper_city = pkg.get('shipperAddress', {}).get('city', 'N/A')
                            shipper_country_code = pkg.get('shipperAddress', {}).get('countryCode', 'N/A')
                            recipient_city = pkg.get('recipientAddress', {}).get('city', 'N/A')
                            recipient_country_code = pkg.get('recipientAddress', {}).get('countryCode', 'N/A')
                            valid_data.append({
                                'tracking_number': tracking_number,
                                'shipper_city': shipper_city,
                                'shipper_country_code': shipper_country_code,
                                'recipient_city': recipient_city,
                                'recipient_country_code': recipient_country_code
                            })

                        # Save the initial results
                        existing_lines = set()
                        if os.path.exists("tracking_numbers.txt"):
                            with open("tracking_numbers.txt", "r") as output_f:
                                existing_lines = set(line.strip() for line in output_f)

                        unique_lines_to_write = set()
                        for pkg in valid_data:
                            new_line = f"{pkg['tracking_number']};{pkg['shipper_city']},{pkg['shipper_country_code']};{pkg['recipient_city']},{pkg['recipient_country_code']}"
                            print(new_line)
                            if new_line not in existing_lines and new_line not in unique_lines_to_write:
                                unique_lines_to_write.add(new_line)

                        if unique_lines_to_write:
                            with open("tracking_numbers.txt", "a") as output_f:
                                for line in unique_lines_to_write:
                                    output_f.write(line + "\n")

                        # Return after processing initial batch
                        await asyncio.sleep(random.uniform(2, 4))
                        browser.request_details['cookies'] = await browser.context.cookies()
                        return random.choice(numbers)

                    except asyncio.TimeoutError:
                        print("Timeout during browser initialization")
                        await browser.reinitialize()
                        continue
                    finally:
                        page.remove_listener("request", handle_request)
                        page.remove_listener("response", handle_shipment_response)
                        await asyncio.sleep(2)

                except Exception as e:
                    print(f"Error during initialization: {e}")
                    await browser.reinitialize()
                    continue

            # Verify we have request details before proceeding
            if not browser.request_details:
                print("No request details available, retrying initialization...")
                await browser.reinitialize()
                continue

            # Prepare the API request
            tracking_info = [
                {"trackNumberInfo": {"trackingCarrier": "", "trackingNumber": str(num), "trackingQualifier": ""}}
                for num in numbers
            ]
            payload = {
                "appDeviceType": "WTRK",
                "appType": "WTRK",
                "supportHTML": True,
                "supportCurrentLocation": True,
                "trackingInfo": tracking_info,
                "uniqueKey": "",
                "guestAuthenticationToken": ""
            }

            print(f"Processing batch with {len(numbers)} numbers using browser {id(browser)}")

            try:

                def cookies_to_header(cookies):
                    # Filter out cookies that shouldn't be included (like those for different domains)
                    fedex_cookies = [cookie for cookie in cookies
                                     if '.fedex.com' in cookie['domain'] or 'fedex.com' in cookie['domain']]

                    # Create cookie string in format "name=value; name2=value2"
                    cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}"
                                               for cookie in fedex_cookies])

                    return cookie_string
                # print(browser.request_details['cookies'])
                # cookies = {k: v for k, v in browser.request_details['cookies'].items() if k.lower() == 'cookie'}
                cookie_header = cookies_to_header(browser.request_details['cookies'])

                def generate_random_accept_language(num_languages=1):
                    # A list of example language codes including regional variants
                    language_codes = [
                        'en-US', 'en-GB', 'es-ES', 'es-MX', 'fr-FR', 'fr-CA', 'de-DE', 'zh-CN',
                        'zh-TW', 'ja-JP', 'ru-RU', 'ru-BY', 'it-IT', 'pt-BR', 'pt-PT', 'ar-SA',
                        'ko-KR', 'nl-NL', 'sv-SE', 'da-DK', 'fi-FI', 'no-NO', 'pl-PL',
                        'tr-TR', 'cs-CZ', 'hu-HU'
                    ]

                    # Randomly select languages
                    selected_languages = random.sample(language_codes, min(num_languages, len(language_codes)))

                    # Create the Accept-Language string
                    accept_language = []
                    for lang in selected_languages:
                        # Randomly assign a quality value (q-value) between 0.5 and 1.0
                        q_value = 0.9
                        # q_value = round(random.uniform(0.4, 0.9), 1)
                        accept_language.append(f"{lang};q={q_value}")

                    # Join the languages into a single string
                    return ', '.join(accept_language)

                headers = browser.request_details['headers']

                headers.update({
                    'accept-language': generate_random_accept_language(),  # Add accept-language header
                    'priority': 'u=1, i',  # Add priority header
                    'sec-fetch-dest': 'empty',  # Add sec-fetch-dest header
                    'sec-fetch-mode': 'cors',  # Add sec-fetch-mode header
                    'sec-fetch-site': 'same-site',  # Add sec-fetch-site header
                    'sec-gpc': '1',  # Add sec-gpc header
                    'sec-ch-ua': browser.profile["sec_ch_ua"],  # Update sec-ch-ua
                    'sec-ch-ua-platform': browser.profile["sec_ch_ua_platform"],
                    'referer': 'https://www.fedex.com/'
                })
                headers['Cookie'] = cookie_header
                # print(headers)
                # Add back the cookies to the new headers
                # headers.update(cookies)
                response = await browser.context.request.fetch(
                    browser.request_details['url'], method="post",
                    data=payload,
                    headers=headers,
                )
                print(f'success {response.status}')
                if response.status == 403:
                    print("Received 403 error, reinitializing browser...")
                    await browser.reinitialize()
                    continue

                json_data = await response.json()
                packages = json_data.get("output", {}).get("packages", [])
                valid_packages = [pkg for pkg in packages if 'errorList' not in pkg]
                valid_data = []

                for pkg in valid_packages:
                    tracking_number = pkg.get('trackingNbr', "")
                    shipper_city = pkg.get('shipperAddress', {}).get('city', 'N/A')
                    shipper_country_code = pkg.get('shipperAddress', {}).get('countryCode', 'N/A')
                    recipient_city = pkg.get('recipientAddress', {}).get('city', 'N/A')
                    recipient_country_code = pkg.get('recipientAddress', {}).get('countryCode', 'N/A')
                    valid_data.append({
                        'tracking_number': tracking_number,
                        'shipper_city': shipper_city,
                        'shipper_country_code': shipper_country_code,
                        'recipient_city': recipient_city,
                        'recipient_country_code': recipient_country_code
                    })

                # Process and save results
                existing_lines = set()
                if os.path.exists("tracking_numbers.txt"):
                    with open("tracking_numbers.txt", "r") as output_f:
                        existing_lines = set(line.strip() for line in output_f)

                unique_lines_to_write = set()
                for pkg in valid_data:
                    new_line = f"{pkg['tracking_number']};{pkg['shipper_city']},{pkg['shipper_country_code']};{pkg['recipient_city']},{pkg['recipient_country_code']}"
                    print(new_line)
                    if new_line not in existing_lines and new_line not in unique_lines_to_write:
                        unique_lines_to_write.add(new_line)

                if unique_lines_to_write:
                    with open("tracking_numbers.txt", "a") as output_f:
                        for line in unique_lines_to_write:
                            output_f.write(line + "\n")

                await asyncio.sleep(random.uniform(2, 4))
                return random.choice(numbers)

            except Exception as e:
                print(f"Request error: {e}")
                if "403" in str(e) or "NoneType" in str(e):
                    print("Error occurred, reinitializing browser...")
                    await browser.reinitialize()
                await asyncio.sleep(random.uniform(1, 2))
                continue

        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(random.uniform(1, 2))
            if attempt == retries - 1:
                return None


async def process_batch(browser_pool, numbers):
    browser = await browser_pool.get_available_browser()
    try:
        result = await asyncio.wait_for(fetch_content(browser, numbers), timeout=100)
        return result
    except asyncio.TimeoutError:
        print("Batch processing timeout")
        return None
    finally:
        await browser_pool.release_browser(browser)


async def main_async(start_number, total_numbers, thread_count):
    browser_pool = BrowserPool(thread_count)
    await browser_pool.initialize()

    try:
        last_checked = load_last_checked_number()
        if last_checked is not None and last_checked > start_number:
            start_number = last_checked

        end_number = start_number + total_numbers
        batches = []
        for i in range((end_number - start_number) // 30):
            numbers = [start_number + j for j in range(i * 30, (i + 1) * 30)]
            batches.append(numbers)

        # Process batches concurrently
        tasks = [process_batch(browser_pool, batch) for batch in batches]
        results = await asyncio.gather(*tasks)

        # Process results
        failed_batches = []
        for batch, result in zip(batches, results):
            if result is not None:
                save_last_checked_number(result)
            else:
                failed_batches.append(batch)

        # Retry failed batches
        if failed_batches:
            print("Retrying failed batches...")
            retry_tasks = [process_batch(browser_pool, batch) for batch in failed_batches]
            retry_results = await asyncio.gather(*retry_tasks)

    finally:
        await browser_pool.cleanup()


def main(start_number, total_numbers, thread_count):
    start_time = time.time()
    asyncio.run(main_async(start_number, total_numbers, thread_count))
    end_time = time.time()

    print(f"Total execution time: {end_time - start_time:.2f} seconds")
    print(f"Cumulative Request Size: {format_bytes(total_cumulative_request_size)}")
    print(f"Cumulative Response Size: {format_bytes(total_cumulative_response_size)}")


# Helper functions remain the same
def format_bytes(size):
    if size == 0:
        return "0 Bytes"
    size_name = ("Bytes", "KB", "MB", "GB")
    i = int(math.log(size, 1024))
    p = pow(1024, i)
    s = round(size / p, 2)
    return f"{s} {size_name[i]}"


def load_last_checked_number():
    if os.path.exists('last_checked.json'):
        with open('last_checked.json', 'r') as f:
            return json.load(f).get("last_number", None)
    return None


def save_last_checked_number(last_number):
    with open('last_checked.json', 'w') as f:
        json.dump({"last_number": last_number}, f)


if __name__ == "__main__":
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    start_number = config.get("start_number", 770495122048)
    total_numbers = config.get("total_numbers", 500000)
    thread_count = config.get("thread_count", 1)

    main(start_number, total_numbers, thread_count)
