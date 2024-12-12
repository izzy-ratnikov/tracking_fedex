import asyncio
import math
import os
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor

from playwright._impl._errors import TargetClosedError
from playwright.async_api import async_playwright

proxy_server = "http://proxy-us.cravenet.com:7070"
proxy_password = '5efecb83-8e4b-46c1-8aea-a44514f23056'

# Cumulative variables to track total traffic
total_cumulative_request_size = 0
total_cumulative_response_size = 0


async def fetch_content(numbers, retries=3):
    global total_cumulative_request_size, total_cumulative_response_size  # Use global to modify outside variables
    selected_number = random.choice(numbers)
    last_five_digits = str(selected_number)[-5:]
    total_request_size = 0
    total_response_size = 0

    for attempt in range(retries):  # Retries for each batch
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=False,
                                                  args=['--disable-blink-features=AutomationControlled'])
                context = await browser.new_context(
                    proxy={
                        "server": proxy_server,
                        "username": f'pool-nflx_us-session-{last_five_digits}',
                        "password": proxy_password
                    }
                )

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

                number_list = ','.join(map(str, numbers))
                url = f'https://www.fedex.com/fedextrack/summary?trknbr={number_list}'
                print(f"Opening URL: {url}")
                page = await context.new_page()
                await page.route("**/*", handle_route)

                shipment_resp_promise = asyncio.Future()

                async def handle_shipment_response(response):
                    try:
                        global total_cumulative_request_size, total_cumulative_response_size
                        sizes = await response.request.sizes()
                        total_cumulative_request_size += sizes['requestBodySize'] + sizes['requestHeadersSize']
                        total_cumulative_response_size += sizes['responseBodySize'] + sizes['responseHeadersSize']
                    except Exception as e:
                        pass
                    if "api.fedex.com/track/v2/shipments" in response.url:
                        if response.status == 200:
                            try:
                                json_data = await response.json()
                            except Exception as json_error:
                                print(f"JSON parsing error: {json_error}")
                                return

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

                            if not shipment_resp_promise.done():  # Ensure the promise is not resolved yet
                                shipment_resp_promise.set_result(valid_data)

                # Attach the response handler
                page.on("response", handle_shipment_response)
                await page.goto(url)

                shipment = await shipment_resp_promise

                existing_lines = set()
                if os.path.exists("tracking_numbers.txt"):
                    with open("tracking_numbers.txt", "r") as output_f:
                        existing_lines = set(line.strip() for line in output_f)

                unique_lines_to_write = set()  # Buffer for unique lines
                for pkg in shipment:
                    # Format the string according to the specified format
                    new_line = f"{pkg['tracking_number']};{pkg['shipper_city']},{pkg['shipper_country_code']};{pkg['recipient_city']},{pkg['recipient_country_code']}"
                    print(new_line)
                    # Add to buffer if the line is unique
                    if new_line not in existing_lines and new_line not in unique_lines_to_write:
                        unique_lines_to_write.add(new_line)

                    with open("tracking_numbers.txt", "a") as output_f:
                        for line in unique_lines_to_write:
                            output_f.write(line + "\n")
                    unique_lines_to_write.clear()

                # Write any remaining unique lines to the file after processing
                if unique_lines_to_write:
                    with open("tracking_numbers.txt", "a") as output_f:
                        for line in unique_lines_to_write:
                            output_f.write(line + "\n")

                with open("last_number.txt", "w") as output_f:
                    output_f.write(f"{selected_number}\n")

                return selected_number

            except asyncio.CancelledError:
                print("Operation was cancelled.")
                return None
            except Exception as e:
                print(f"An error occurred: {e}")
                return None
            finally:
                try:
                    await browser.close()
                except Exception as close_error:
                    print(f"Error closing browser: {close_error}")


async def run_fetch_content(numbers):
    return await asyncio.wait_for(fetch_content(numbers), timeout=100)  # Set your desired timeout here


def run_playwright(numbers):
    try:
        return asyncio.run(run_fetch_content(numbers))
    except Exception as e:
        print(f"Error in run_playwright: {e}")
        return None


def load_last_checked_number():
    if os.path.exists('last_checked.json'):
        with open('last_checked.json', 'r') as f:
            return json.load(f).get("last_number", None)
    return None


def save_last_checked_number(last_number):
    with open('last_checked.json', 'w') as f:
        json.dump({"last_number": last_number}, f)


def format_bytes(size):
    """Convert bytes to a more readable format (GB, MB, etc.)."""
    if size == 0:
        return "0 Bytes"
    size_name = ("Bytes", "KB", "MB", "GB")
    i = int(math.log(size, 1024))
    p = pow(1024, i)
    s = round(size / p, 2)
    return f"{s} {size_name[i]}"


def main(start_number, total_numbers, thread_count):
    last_checked = load_last_checked_number()
    # Determine the starting point
    if last_checked is not None and last_checked > start_number:
        start_number = last_checked  # Start from the last checked number if it's greater

    end_number = start_number + total_numbers

    numbers_to_process = []
    failed_numbers = []

    start_time = time.time()

    # First round of processing
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = []

        for i in range((end_number - start_number) // 30):
            numbers = [start_number + j for j in range(i * 30, (i + 1) * 30)]
            numbers_to_process.append(numbers)
            futures.append(executor.submit(run_playwright, numbers))

        for future in futures:
            result = future.result()
            if result is not None:
                print("Content fetched successfully.")
                save_last_checked_number(result)
            else:
                failed_numbers.extend(numbers)

    # Retry failed numbers
    if failed_numbers:
        print("Retrying failed numbers...")
        # Create a new executor for retries
        with ThreadPoolExecutor(max_workers=thread_count) as retry_executor:
            retry_futures = []
            for i in range(0, len(failed_numbers), 30):
                batch = failed_numbers[i:i + 30]
                retry_futures.append(retry_executor.submit(run_playwright, batch))

            for retry_future in retry_futures:
                result = retry_future.result()  # Wait for retries to complete
                if result is not None:
                    print("Retry successful for a failed number.")

    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total execution time: {total_time:.2f} seconds")

    print(f"Cumulative Request Size: {format_bytes(total_cumulative_request_size)}")
    print(f"Cumulative Response Size: {format_bytes(total_cumulative_response_size)}")


if __name__ == "__main__":
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    start_number = config.get("start_number", 770495122048)
    total_numbers = config.get("total_numbers", 500000)
    thread_count = config.get("thread_count", 1)

    main(start_number, total_numbers, thread_count)
