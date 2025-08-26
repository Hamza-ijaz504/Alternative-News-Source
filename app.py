# app.py (Final Version, compatible with the intelligent processor)

from flask import Flask, render_template, request
import processor

# Create an instance of the Flask application
app = Flask(__name__)

# --- One-time setup when the server starts ---
# The NLTK setup and the spaCy model loading will happen once when processor.py is imported.
print("Initializing NLP models...")
# This line is not strictly needed as importing does the work, but it's good for clarity.
# If you wanted to be explicit, you could call setup_nltk() here, but the test block in processor.py
# and the global loading of spaCy handle it.
print("Initialization complete.")
# --- End of setup ---


@app.route('/')
def index():
    """Renders the main homepage with the input form."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Handles the form submission, runs the full NLP pipeline, and renders the results.
    """
    url = request.form['url']
    
    # 1. Fetch the original article's content
    title, raw_text = processor.fetch_article_text(url)
    
    # Handle fetching errors gracefully
    if not raw_text:
        error_message = "Error: Could not fetch or parse the article from the initial URL. The website might be blocking automated requests or requires JavaScript to load its content."
        return render_template('error.html', error_message=error_message)

    # 2. Perform the core NLP analysis on the original article
    sentiment = processor.analyze_sentiment_from_text(raw_text)
    topics = processor.analyze_topics_from_text(raw_text)
    
    # 3. Find alternative articles using the new intelligent search strategy
    # *** THIS IS THE KEY CHANGE: Pass raw_text to the function ***
    alternative_articles = processor.find_alternative_articles(topics, raw_text)
    
    # 4. Analyze sentiment for each of the successfully found alternative articles
    successful_alternatives = []
    if alternative_articles:
        for article in alternative_articles:
            print(f"Fetching and analyzing alternative: {article['url']}")
            _ , alt_raw_text = processor.fetch_article_text(article['url'])
            if alt_raw_text:
                article['sentiment'] = processor.analyze_sentiment_from_text(alt_raw_text)
                successful_alternatives.append(article)
            else:
                print(f"--> Failed to fetch content for: {article['title']}")
    
    # 5. Render the final results page with all the collected data
    return render_template(
        'results.html', 
        article_title=title, 
        sentiment=sentiment, 
        topics=topics,
        alternative_articles=successful_alternatives
    )


if __name__ == '__main__':
    # When running the app, it's good practice to run the NLTK setup first
    # to ensure all resources are downloaded before the server starts accepting requests.
    processor.setup_nltk()
    app.run(debug=True)