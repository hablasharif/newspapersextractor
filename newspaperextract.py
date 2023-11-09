import streamlit as st
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor

# Define a regular expression pattern to match English text
english_pattern = re.compile(r'[a-zA-Z\s]+')

async def fetch_url_content(session, url, max_retries=3, timeout=60):
    for retry in range(max_retries):
        try:
            async with session.get(url, timeout=timeout) as response:
                response.raise_for_status()
                html = await response.text()
                return html
        except aiohttp.ClientError as e:
            st.warning(f"Error fetching {url}, Retry {retry + 1}/{max_retries}: {e}")
        except asyncio.TimeoutError:
            st.warning(f"Timeout fetching {url}, Retry {retry + 1}/{max_retries}")

    return None

async def extract_paragraphs(url):
    async with aiohttp.ClientSession() as session:
        html = await fetch_url_content(session, url)
        if html is None:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        p_tags = soup.find_all('p')
        content = [p.get_text() for p in p_tags]

        # Filter English text and remove punctuation
        filtered_content = []
        for paragraph in content:
            english_text = " ".join(re.findall(english_pattern, paragraph))
            filtered_content.append(english_text)

        return filtered_content

async def process_url(url, timeout=10):
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            content = await extract_paragraphs(url)
            return " ".join(content)
    except Exception as e:
        st.error(f"Error processing {url}: {e}")
        return ""

async def main(urls, timeout=60):
    total_result = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(process_url(url, timeout)) for url in urls]

        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            total_result.append(result)

    return "\n".join(total_result)

if __name__ == "__main__":
    st.title("Streamlit Web Scraper")

    # User input for URLs
    user_urls = st.text_area("Enter URLs (one per line)", "")
    urls = user_urls.split('\n')

    if st.button("Scrape URLs"):
        st.markdown("### Scraping URLs")
        st.write(urls)

        st.markdown("### Results")
        timeout = st.number_input("Timeout (seconds)", value=60)
        progress_bar = st.progress(0)

        # Run the main function with the specified timeout and get the concatenated results
        total_results = asyncio.run(main(urls, timeout))

        # Display the results in one output box
        st.text_area("Results", total_results, height=400)
        st.success("Scraping Complete!")  
