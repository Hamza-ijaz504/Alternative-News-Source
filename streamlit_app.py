# streamlit_app.py

import streamlit as st
import processor # This is your main NLP engine

# --- Page Configuration (makes the app look good) ---
st.set_page_config(
    page_title="Alternative News Analyzer",
    page_icon="📰",
    layout="wide"
)

# --- One-time Setup (cached for efficiency) ---
# This function will run only once to download the necessary models.
@st.cache_resource
def load_models_and_setup():
    """
    Performs one-time setup of NLTK and downloads the spaCy model.
    Using @st.cache_resource ensures this only runs once when the app starts.
    """
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

# Run the setup function
load_models_and_setup()

# --- Main App Interface ---
st.title("📰 Alternative News Analyzer")
st.markdown("Enter the URL of a news article to discover different perspectives. The system will analyze its topics and sentiment, then find related articles from various sources.")

# --- Input Form ---
with st.form(key='url_form'):
    url_input = st.text_input(
        "Enter News Article URL", 
        placeholder="https://www.bbc.com/news/..."
    )
    submit_button = st.form_submit_button(label='Analyze Article')

# --- Processing Logic (runs only when the button is pressed and URL is provided) ---
if submit_button and url_input:
    # Show a spinner while the analysis is in progress
    with st.spinner("Analyzing article... This may take a moment."):
        
        # 1. Fetch the original article
        title, raw_text = processor.fetch_article_text(url_input)

        if not raw_text:
            st.error("Error: Could not fetch or parse the article from the provided URL. The website might be blocking requests or is not a standard news article.")
        else:
            st.success(f"Successfully fetched article: **{title}**")

            # 2. Perform NLP analysis
            sentiment = processor.analyze_sentiment_from_text(raw_text)
            topics = processor.analyze_topics_from_text(raw_text)

            # --- Display Results for the Original Article ---
            st.header("Original Article Analysis")
            
            # Display Sentiment in columns
            col1, col2, col3, col4 = st.columns(4)
            col1.metric(label="Negative", value=f"{sentiment['neg']:.3f}")
            col2.metric(label="Neutral", value=f"{sentiment['neu']:.3f}")
            col3.metric(label="Positive", value=f"{sentiment['pos']:.3f}")
            col4.metric(label="Compound Score", value=f"{sentiment['compound']:.3f}")
            
            # Display Topics
            st.subheader("Extracted Topics")
            if topics:
                for topic in topics:
                    st.markdown(f"- **Topic:** {', '.join(topic['keywords'])}")
            else:
                st.write("No distinct topics could be extracted. The article may be too short or homogenous.")

            # --- Find and Display Alternative Articles ---
            st.header("Alternative Articles")
            
            # Show a nested spinner for this specific part
            with st.spinner("Searching for alternative articles..."):
                alternative_articles = processor.find_alternative_articles(topics, raw_text)

                if not alternative_articles:
                    st.write("No alternative articles could be found for the extracted topics.")
                else:
                    for article in alternative_articles:
                        # Analyze sentiment for each alternative
                        _, alt_raw_text = processor.fetch_article_text(article['url'])
                        if alt_raw_text:
                            article['sentiment'] = processor.analyze_sentiment_from_text(alt_raw_text)
                        else:
                            article['sentiment'] = None
                        
                        # Display each article in a nice container
                        with st.container(border=True):
                            st.subheader(f"[{article['source']}] {article['title']}")
                            st.markdown(f"[Read full article]({article['url']}) - Published: {article['publishedAt']}")
                            if article['sentiment']:
                                c1, c2, c3, c4 = st.columns(4)
                                c1.metric("Negative", f"{article['sentiment']['neg']:.2f}")
                                c2.metric("Neutral", f"{article['sentiment']['neu']:.2f}")
                                c3.metric("Positive", f"{article['sentiment']['pos']:.2f}")
                                c4.metric("Compound", f"{article['sentiment']['compound']:.2f}")
                            else:
                                st.write("Could not analyze sentiment for this article.")