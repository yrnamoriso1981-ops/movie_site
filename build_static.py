import os
import shutil
from app import app, get_movies


OUTPUT = "netlify"


def save_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "wb") as f:
        f.write(content)


# Clean previous build
if os.path.exists(OUTPUT):
    shutil.rmtree(OUTPUT)

os.makedirs(OUTPUT)

client = app.test_client()
movies = get_movies()


# --------------------------------
# HOME
# --------------------------------

response = client.get("/")

save_file(
    f"{OUTPUT}/index.html",
    response.data
)


# --------------------------------
# LATEST
# --------------------------------

response = client.get("/latest")

save_file(
    f"{OUTPUT}/latest/index.html",
    response.data
)


# --------------------------------
# TOP RATED
# --------------------------------

response = client.get("/top-rated")

save_file(
    f"{OUTPUT}/top-rated/index.html",
    response.data
)


# --------------------------------
# ALL MOVIES
# --------------------------------

response = client.get("/movies")

save_file(
    f"{OUTPUT}/movies/index.html",
    response.data
)


# --------------------------------
# MOVIE DETAIL PAGES
# --------------------------------

for movie in movies:

    detail_url = movie.get("detail_url", "")

    if not detail_url.startswith("/movie/"):
        continue

    movie_id = detail_url.split("/")[-1]

    response = client.get(detail_url)

    if response.status_code == 200:

        save_file(
            f"{OUTPUT}/movie/{movie_id}/index.html",
            response.data
        )


# --------------------------------
# ROBOTS.TXT
# --------------------------------

robots = """User-agent: *
Allow: /

Sitemap: https://movie-site-6cup.onrender.com/sitemap.xml
"""

save_file(
    f"{OUTPUT}/robots.txt",
    robots.encode("utf-8")
)


# --------------------------------
# GOOGLE SEARCH CONSOLE
# --------------------------------

google_verification = (
    "google-site-verification: "
    "google3efed764d6558e52.html"
)

save_file(
    f"{OUTPUT}/google3efed764d6558e52.html",
    google_verification.encode("utf-8")
)


# --------------------------------
# SITEMAP
# --------------------------------

base_url = "https://movie-site-6cup.onrender.com"

urls = [
    base_url + "/"
]

for movie in movies:

    detail_url = movie.get("detail_url", "")

    if detail_url.startswith("/movie/"):
        urls.append(base_url + detail_url)


xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

for url in urls:
    xml += f"    <url><loc>{url}</loc></url>\n"

xml += "</urlset>"

save_file(
    f"{OUTPUT}/sitemap.xml",
    xml.encode("utf-8")
)


print(f"Static build complete: {len(movies)} movies")
