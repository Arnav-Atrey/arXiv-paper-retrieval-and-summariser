import streamlit as st
from PyPDF2 import PdfReader
import requests
from bs4 import BeautifulSoup
import urllib.parse
from transformers import pipeline
import re

def search_arxiv(query):
    url = f"https://arxiv.org/search/?query={query}&searchtype=all&source=header"
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    else:
        return None

def get_paper_with_most_highlighted_words(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    papers = soup.find_all('li', class_='arxiv-result')
    
    max_highlighted_words = 0
    best_paper_url = None
    
    for paper in papers:
        title_span = paper.find('p', class_='title is-5 mathjax')
        if title_span:
            highlighted_words = len(title_span.find_all('span', class_='search-hit mathjax'))
            if highlighted_words > max_highlighted_words:
                max_highlighted_words = highlighted_words
                paper_link = paper.find('p', class_='list-title').find('a')['href']
                paper_number = paper_link.split('/')[-1]
                best_paper_url = "https://arxiv.org/pdf/" + paper_number
    
    return best_paper_url

def download_paper(paper_url, save_path):
    response = requests.get(paper_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        st.success("Paper downloaded successfully!")
    else:
        st.error("Failed to download paper.")

def retrieve_paper(query, save_path):
    search_results = search_arxiv(query)
    if search_results:
        paper_url = get_paper_with_most_highlighted_words(search_results)
        if paper_url:
            download_paper(paper_url, save_path)
        else:
            st.warning("No papers found for the given query.")
    else:
        st.error("Failed to retrieve search results.")

def clean_text(text):
    # Remove references section
    text = re.sub(r'References\s*\d*\s*[\s\S]*', '', text)
    # Remove footnotes
    text = re.sub(r'\[\d+\]', '', text)
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def summarize_paper(filename):
    reader = PdfReader(filename)
    paper_text = ''.join(page.extract_text() for page in reader.pages)
    cleaned_text = clean_text(paper_text)
    
    # Define the maximum number of words to summarize in each chunk
    max_words_per_chunk = 2048
    max_summary_length = 150
    
    summarizer = pipeline("summarization")
    
    start_idx = 0
    while start_idx < len(cleaned_text):
        # Extract a chunk of text to summarize
        chunk_to_summarize = cleaned_text[start_idx:start_idx + max_words_per_chunk]
        
        # Summarize the chunk of text
        summary = summarizer(chunk_to_summarize, max_length=max_summary_length, min_length=30, do_sample=False)[0]['summary_text']
        
        # Print the summary for the current chunk
        st.write(summary)
        
        # Move the start index to the next chunk
        start_idx += max_words_per_chunk
    st.success("Finished Summarising")

def main():
    try:
        st.title("Paper retrieval and Summarizer")
        query = st.text_input("Enter the title of the paper:")
        if st.button("Search and Summarize"):
            with st.spinner("Searching and Summarizing..."):
                save_path = r"C:\Users\Arnav\Downloads\downloaded.pdf"
                query_encoded = urllib.parse.quote(query)
                retrieve_paper(query_encoded, save_path)
                summarize_paper(save_path)
    except Exception as e:
        st.error(e)

if __name__ == "__main__":
    main()