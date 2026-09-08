from flask import Flask, render_template, request
import csv
import os
from datetime import datetime

app = Flask(__name__)

CSV_FILE = os.path.join("data", "movie_details.csv")


def get_movies():
    movies = []

    with open(CSV_FILE, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for movie in reader:
            movie_url = str(movie["url"])

            # Get Cinejoy movie ID
            movie_id = movie_url.split("/")[-1].split("-")[0]

            # Direct Cinejoy watch URL
            movie["watch_url"] = f"https://cinejoy.to/watch/movie/{movie_id}"

            # Our own movie detail URL
            movie["detail_url"] = f"/movie/{movie_id}"

            movies.append(movie)

    return movies


def release_date_value(movie):
    """
    Convert release date into a sortable date.
    Unknown/invalid dates go to the bottom.
    """

    date_text = movie.get("release_date", "").strip()

    if not date_text:
        return datetime.min

    date_formats = [
        "%b %d, %Y",
        "%B %d, %Y",
        "%Y-%m-%d",
        "%Y"
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(date_text, date_format)
        except ValueError:
            continue

    return datetime.min


def rating_value(movie):
    """
    Convert movie rating to a number.
    Unknown ratings become 0.
    """

    try:
        return float(movie.get("rating", 0) or 0)
    except (ValueError, TypeError):
        return 0


# HOME + SEARCH
@app.route("/")
def home():

    movies = get_movies()

    query = request.args.get("q", "").strip()

    if query:

        # First try exact title match
        exact_matches = [
            movie
            for movie in movies
            if query.lower() == movie["title"].strip().lower()
        ]

        if exact_matches:
            movies = exact_matches

        else:
            # If no exact match, use partial search
            movies = [
                movie
                for movie in movies
                if query.lower() in movie["title"].lower()
            ]

        page_title = f'Search Results for "{query}"'

    else:
        page_title = "Latest Movies"

    return render_template(
        "index.html",
        movies=movies,
        query=query,
        page_title=page_title
    )


# LATEST MOVIES
@app.route("/latest")
def latest():

    movies = get_movies()

    movies = sorted(
        movies,
        key=release_date_value,
        reverse=True
    )

    return render_template(
        "index.html",
        movies=movies,
        query="",
        page_title="Latest Movies"
    )


# TOP RATED MOVIES
@app.route("/top-rated")
def top_rated():

    movies = get_movies()

    movies = sorted(
        movies,
        key=rating_value,
        reverse=True
    )

    return render_template(
        "index.html",
        movies=movies,
        query="",
        page_title="Top Rated Movies"
    )


# ALL MOVIES
@app.route("/movies")
def movies_page():

    movies = get_movies()

    return render_template(
        "index.html",
        movies=movies,
        query="",
        page_title="All Movies"
    )


# MOVIE DETAIL PAGE
@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id):

    movies = get_movies()

    for movie in movies:

        movie_url = str(movie["url"])
        movie_id_from_url = movie_url.split("/")[-1].split("-")[0]

        if movie_id_from_url == str(movie_id):

            return render_template(
                "movie.html",
                movie=movie
            )

    return "Movie not found", 404


# GOOGLE SEARCH CONSOLE VERIFICATION
@app.route("/google3efed764d6558e52.html")
def google_verification():

    return "google-site-verification: google3efed764d6558e52.html"


# ROBOTS.TXT
@app.route("/robots.txt")
def robots():

    return """
User-agent: *
Allow: /

Sitemap: https://movie-site-6cup.onrender.com/sitemap.xml
""", 200, {
        "Content-Type": "text/plain"
    }


# SITEMAP
@app.route("/sitemap.xml")
def sitemap():

    movies = get_movies()

    urls = [
        "https://movie-site-6cup.onrender.com/"
    ]

    for movie in movies:

        urls.append(
            "https://movie-site-6cup.onrender.com"
            + movie["detail_url"]
        )

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for url in urls:

        xml += f"    <url><loc>{url}</loc></url>\n"

    xml += "</urlset>"

    return xml, 200, {
        "Content-Type": "application/xml"
    }


# RUN SERVER
if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )