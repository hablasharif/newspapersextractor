import streamlit as st
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor

# Define a regular expression pattern to match English text
english_pattern = re.compile(r'[a-zA-Z\s]+')

async def fetch_url_content(session, url, max_retries=3, timeout=10):
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

async def process_url(url):
    try:
        content = await extract_paragraphs(url)
        return " ".join(content)
    except Exception as e:
        st.error(f"Error processing {url}: {e}")
        return ""

async def main(urls):
    total_words = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(process_url(url)) for url in urls]

        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            words = result.split()
            total_words.extend(words)

    with st.beta_expander("View Results"):
        st.write(" ".join(total_words))

if __name__ == "__main__":
    st.title("Streamlit Web Scraper")

    # User input for URLs
    user_urls = st.text_area("Enter URLs (one per line)", "")
    urls = user_urls.split('\n')

    if st.button("Scrape URLs"):
        st.markdown("### Scraping URLs")
        st.write(urls)

        st.markdown("### Progress")
        progress_bar = st.progress(0)

        for i, url in enumerate(urls):
            st.write(f"Processing URL: {url}")
            asyncio.run(main([url]))
            progress_bar.progress((i + 1) / len(urls))

        st.success("Scraping Complete!")
