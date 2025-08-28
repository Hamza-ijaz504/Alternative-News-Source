# streamlit_app.py (Definitive Final Version with Multi-Stage UI/UX)

import streamlit as st
import processor # Your main NLP engine
import spacy # Needed for the setup function
import nltk

# --- Page Configuration ---
st.set_page_config(
    page_title="Alternative News Analyzer",
    page_icon="📰",
    layout="centered" # Use centered layout for a cleaner look
)

# --- One-time Setup ---
@st.cache_resource
def load_models_and_setup():
    print("Performing one-time setup of NLP models...")
    processor.setup_nltk()
    try:
        spacy.load("en_core_web_sm")
        print("spaCy model 'en_core_web_sm' is already available.")
    except OSError:
        print("spaCy model not found. Downloading 'en_core_web_sm'...")
        spacy.cli.download("en_core_web_sm")
        print("spaCy model downloaded successfully.")
    return True

load_models_and_setup()

# --- Session State Initialization ---
# This is the app's "memory" to track which screen to show.
if 'stage' not in st.session_state:
    st.session_state.stage = 'input'

# --- Helper Function for Displaying Colorful Results ---
def display_results_card(article, is_original=False):
    if is_original:
        st.header("Original Article Analysis")
    else:
        st.subheader(f"[{article['source']}] {article['title']}")
        st.markdown(f"[Read full article]({article['url']}) - Published: {article['publishedAt']}")

    if article.get('sentiment'):
        sentiment = article['sentiment']
        
        # Define colors based on sentiment strength
        neg_color = f"rgba(229, 62, 62, {sentiment['neg'] + 0.1})"
        neu_color = f"rgba(113, 128, 144, {sentiment['neu'] * 0.5 + 0.1})" # Muted neutral
        pos_color = f"rgba(56, 178, 172, {sentiment['pos'] + 0.1})"
        
        comp_val = sentiment['compound']
        if comp_val >= 0.05: comp_bg = "rgba(56, 178, 172, 0.2)"
        elif comp_val <= -0.05: comp_bg = "rgba(229, 62, 62, 0.2)"
        else: comp_bg = "rgba(113, 128, 144, 0.1)"

        # Custom HTML and CSS for the colorful metric cards
        st.markdown(f"""
        <div style="display: flex; justify-content: space-around; text-align: center; gap: 10px; margin-top: 10px;">
            <div style="background-color: {neg_color}; padding: 10px; border-radius: 8px; flex-grow: 1;">
                <div style="font-size: 0.9em; color: #333;">Negative</div>
                <div style="font-size: 1.5em; font-weight: 600;">{sentiment['neg']:.3f}</div>
            </div>
            <div style="background-color: {neu_color}; padding: 10px; border-radius: 8px; flex-grow: 1;">
                <div style="font-size: 0.9em; color: #333;">Neutral</div>
                <div style="font-size: 1.5em; font-weight: 600;">{sentiment['neu']:.3f}</div>
            </div>
            <div style="background-color: {pos_color}; padding: 10px; border-radius: 8px; flex-grow: 1;">
                <div style="font-size: 0.9em; color: #333;">Positive</div>
                <div style="font-size: 1.5em; font-weight: 600;">{sentiment['pos']:.3f}</div>
            </div>
            <div style="background-color: {comp_bg}; padding: 10px; border-radius: 8px; flex-grow: 1;">
                <div style="font-size: 0.9em; color: #333;">Compound</div>
                <div style="font-size: 1.5em; font-weight: 600;">{sentiment['compound']:.3f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.write("Could not analyze sentiment for this article.")

# --- Main App Logic based on Stage ---

# STAGE 1: SHOW THE INPUT SCREEN
if st.session_state.stage == 'input':
    st.title("📰 Alternative News Analyzer")
    st.markdown("Enter the URL of a news article to discover different perspectives. The system will analyze its topics and sentiment, then find related articles from various sources.")
    
    url_input = st.text_input("Enter News Article URL", placeholder="https://www.bbc.com/news/...")
    
    if st.button('Analyze Article'):
        if url_input:
            st.session_state.url = url_input
            st.session_state.stage = 'processing'
            st.rerun() # Rerun the script to move to the next stage
        else:
            st.warning("Please enter a URL to analyze.")

# STAGE 2: SHOW THE PROCESSING SCREEN
elif st.session_state.stage == 'processing':
    st.title("🔍 Analyzing Article...")
    st.markdown("Please wait while the system performs the analysis. This involves:")
    st.text("1. Fetching the article content...")
    st.text("2. Analyzing topics and sentiment...")
    st.text("3. Searching for alternative articles...")
    st.text("4. Analyzing each alternative article...")
    
    with st.spinner("Processing... This can take up to a minute."):
        # Perform all the heavy lifting
        title, raw_text = processor.fetch_article_text(st.session_state.url)
        
        if not raw_text:
            st.session_state.error = "Could not fetch the article. The URL might be invalid, or the site may be blocking access."
            st.session_state.stage = 'error'
            st.rerun()
        else:
            # Store results in session state
            st.session_state.original_article = {'title': title, 'sentiment': processor.analyze_sentiment_from_text(raw_text)}
            st.session_state.topics = processor.analyze_topics_from_text(raw_text)
            
            alternatives = processor.find_alternative_articles(st.session_state.topics, raw_text)
            processed_alternatives = []
            for article in alternatives:
                _, alt_raw_text = processor.fetch_article_text(article['url'])
                if alt_raw_text:
                    article['sentiment'] = processor.analyze_sentiment_from_text(alt_raw_text)
                    processed_alternatives.append(article)
            
            st.session_state.alternatives = processed_alternatives
            st.session_state.stage = 'results'
            st.rerun() # Rerun to show the results page

# STAGE 3: SHOW THE RESULTS SCREEN
elif st.session_state.stage == 'results':
    st.title("📊 Analysis Results")
    
    # Display Original Article Results
    display_results_card(st.session_state.original_article, is_original=True)
    
    # Display Topics
    st.header("Extracted Topics")
    if st.session_state.topics:
        for topic in st.session_state.topics:
            st.markdown(f"- {', '.join(topic['keywords'])}")
    else:
        st.info("No distinct topics could be extracted from this article.")
        
    # Display Alternative Articles
    st.header("Alternative Articles")
    if st.session_state.alternatives:
        for article in st.session_state.alternatives:
            with st.container(border=True):
                display_results_card(article)
    else:
        st.info("No alternative articles could be found for the extracted topics.")

    # Button to go back to the start
    if st.button("Analyze Another Article"):
        st.session_state.stage = 'input'
        # Clear out old data
        keys_to_clear = ['url', 'original_article', 'topics', 'alternatives', 'error']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# (Optional) Error Stage
elif st.session_state.stage == 'error':
    st.error(st.session_state.error)
    if st.button("Try Again"):
        st.session_state.stage = 'input'
        if 'error' in st.session_state:
            del st.session_state['error']
        st.rerun()