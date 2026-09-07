from flask import Flask, render_template
import csv
import os

app = Flask(__name__)

CSV_FILE = os.path.join("data", "movies_clean.csv")


def get_movies():
    movies = []

    with open(CSV_FILE, "r", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        for movie in reader:
            movies.append(movie)

    return movies


@app.route("/")
def home():
    movies = get_movies()

    return render_template(
        "index.html",
        movies=movies
    )


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


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )