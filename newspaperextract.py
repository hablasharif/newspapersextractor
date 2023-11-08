import streamlit as st
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor
from collections import Counter

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
    total_result = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        loop = asyncio.get_event_loop()
        tasks = [loop.create_task(process_url(url)) for url in urls]

        for i, completed_task in enumerate(asyncio.as_completed(tasks), 1):
            result = await completed_task
            total_result.append(result)

            # Update progress bar
            progress_percent = i / len(urls) * 100
            st.progress(progress_percent)

    # Combine results into a single string
    combined_results = " ".join(total_result)

    # Extract unique words
    unique_words = Counter(combined_results.split())

    return combined_results, unique_words

if __name__ == "__main__":
    st.title("Streamlit Web Scraper")

    # User input for URLs
    user_urls = st.text_area("Enter URLs (one per line)", "")
    urls = user_urls.split('\n')

    if st.button("Scrape URLs"):
        st.markdown("### Scraping URLs")
        st.write(urls)

        st.markdown("### Original Texts")
        original_texts = asyncio.run(main(urls))[0]
        st.text_area("Original Texts", original_texts, height=400)

        st.markdown("### Results")
        # Run the main function and get the unique words
        unique_words = asyncio.run(main(urls))[1]

        # Display the total number of unique words
        st.write(f"Total Unique Words: {len(unique_words)}")

        # Display the unique words in a text area
        st.text_area("Unique Words", "\n".join(f"{word}: {count}" for word, count in unique_words.items()), height=400)
        st.success("Scraping Complete!")
