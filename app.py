from flask import Flask, render_template
from flask import request, jsonify, url_for
from textblob import TextBlob
from googleapiclient.discovery import build
from flask import Flask, render_template, request, redirect, url_for
from textblob import TextBlob
import csv
import pandas as pd
import chardet
import os


app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'static'

@app.route('/')
def landing_page():
    return render_template("index.html")

@app.route('/index.html')
def home():
    return render_template("index.html")
    
@app.route('/about.html')
def about():
    return render_template("about.html")
@app.route('/service.html')
def service():
    return render_template("service.html")
@app.route('/contact.html')
def contactus():
    return render_template("contact.html")

@app.route('/')
def index():
    return render_template('index.html')

# --------------------------For Text analysis----------------------------------#

   

# Function to analyze sentiment using TextBlob


@app.route('/text_analysis', methods=["GET", "POST"])
def text_analysis():
    sentiment_category = None
    if request.method == "POST":
        text = request.form.get("text")
        
        # Check if 'text' is not None and is a valid string
        if text is not None and isinstance(text, str):
            # Perform sentiment analysis on the provided text
            sentiment_category = perform_sentiment_analysis(text)
    
    return render_template("text_analysis.html", sentiment_category=sentiment_category)


def perform_sentiment_analysis(text):
    # Check if 'text' is not None and is a valid string
    if text is not None and isinstance(text, str):
        # Perform sentiment analysis using TextBlob
        analysis = TextBlob(text)
    
        # Determine sentiment category based on polarity
        sentiment_polarity = analysis.sentiment.polarity
        if sentiment_polarity > 0:
            sentiment_category = "Positive"
        elif sentiment_polarity < 0:
            sentiment_category = "Negative"
        else:
            sentiment_category = "Neutral"
    
        return sentiment_category
    else:
        # Handle the case when 'text' is None or not a valid string
        return "Invalid input"
# End of text text_analysis

#-----------Youtube analysis-----------------------#
@app.route("/youtube_analysis", methods=["GET", "POST"])
def youtube_analysis():
    error_message = None  # Initialize error message variable
    
    if request.method == "POST":
        video_url = request.form["youtubeurl"]
        video_id = video_url[32:]
        api_key = "AIzaSyDBEMg-4ud4YdoIRPCa3pjs8S8HaSi-0hg"  # Replace with your API key

        # Create a YouTube API service instance
        youtube = build('youtube', 'v3', developerKey=api_key)

        try:
            # Attempt to get video comments
            video_comments = get_all_video_comments(youtube, part='snippet', videoId=video_id, textFormat='plainText')
            sentiments = []

            for comment in video_comments:
                analysis = TextBlob(comment)
                sentiment_score = analysis.sentiment.polarity

                if sentiment_score > 0:
                    sentiment = "Positive"
                elif sentiment_score < 0:
                    sentiment = "Negative"
                else:
                    sentiment = "Neutral"

                sentiments.append(sentiment)

            comments_with_sentiments = [{"comment": comment, "sentiment": sentiment} for comment, sentiment in
                                         zip(video_comments, sentiments)]

            # Calculate overall sentiment score
            numeric_sentiments = [score for score in sentiments if isinstance(score, (int, float))]
            sentiment_score = sum(numeric_sentiments) / len(numeric_sentiments) if numeric_sentiments else 0

            return render_template("youtube_analysis.html", sentiment_score=sentiment_score,
                                   comments_with_sentiments=comments_with_sentiments, length = len(video_comments))

        except TimeoutError as e:
            # Handle the timeout error here, set the error message
            error_message = "API request timed out"

    return render_template("youtube_analysis.html", error_message=error_message)

import time

def get_all_video_comments(service, **kwargs):
    comments = []
    next_page_token = None
    timeout = time.time() + 360  # Set a timeout of 2 minutes (adjust as needed)

    while True:
        if time.time() > timeout:
            raise TimeoutError("API request timed out")
        kwargs['maxResults'] = 1000  # You can adjust this value

        results = service.commentThreads().list(**kwargs, pageToken=next_page_token).execute()
        for item in results['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            comments.append(comment)

        # Check if there are more pages of comments
        next_page_token = results.get('nextPageToken')
        if not next_page_token:
            break

    return comments
#--------------------CSV File analysis--------------#
def analyze_sentiment(text):
    analysis = TextBlob(text)
    sentiment_score = analysis.sentiment.polarity
    return "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"

@app.route("/csv_analysis", methods=["GET", "POST"])
def csv_analysis():
     if request.method == "POST":
        # Check if a file is uploaded
        if "csv_file" not in request.files:
            return redirect(request.url)
        
        csv_file = request.files["csv_file"]
        
        if csv_file.filename == "":
            return redirect(request.url)
        
        try:
            # Save the uploaded CSV file temporarily
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            csv_filename = os.path.join("uploads", "temp.csv")
            csv_file.save(csv_filename)

            # Check the encoding of the CSV file using chardet
            with open(csv_filename, 'rb') as f:
                result = chardet.detect(f.read())
            encoding = result['encoding']

            # Read the CSV file using the detected encoding
            df = pd.read_csv(csv_filename, encoding=encoding)

            # Perform sentiment analysis on the CSV data
            comment_list = df['Text']
            comment_list = list(comment_list)
            sentiments = []
            for comment in comment_list:
                sentiment = analyze_sentiment(comment)
                sentiments.append(sentiment)

            # Calculate overall sentiment score
            positive_count = sentiments.count("Positive")
            negative_count = sentiments.count("Negative")
            neutral_count = sentiments.count("Neutral")

            # Render the results template
            return render_template("csv_analysis.html", positive_count=positive_count, negative_count=negative_count, neutral_count=neutral_count)

        except Exception as e:
            return f"Error processing the file: {str(e)}"
     return render_template("csv_analysis.html")

if __name__ == "__main__":
    app.run(debug = True)