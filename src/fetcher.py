import asyncio
import os
import random

total_cumulative_request_size = 0
total_cumulative_response_size = 0


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
