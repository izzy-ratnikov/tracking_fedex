import json
import time
import asyncio
from src.browser.browser_pool import BrowserPool
from src.fetcher import process_batch, total_cumulative_request_size, total_cumulative_response_size
from src.utils import save_last_checked_number, load_last_checked_number, format_bytes

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


if __name__ == "__main__":
    with open('config/config.json', 'r') as config_file:
        config = json.load(config_file)

    start_number = config.get("start_number", 770495122048)
    total_numbers = config.get("total_numbers", 500000)
    thread_count = config.get("thread_count", 1)

    main(start_number, total_numbers, thread_count)