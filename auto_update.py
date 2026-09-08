from dotenv import load_dotenv
import os
import csv
import requests
import subprocess
import shutil
import time
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")

if not API_KEY:
    print("TMDB API KEY NOT FOUND")
    raise SystemExit

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

MASTER_FILE = os.path.join("data", "movie_details.csv")
BACKUP_FILE = os.path.join(
    "data",
    "movie_details_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
)

FRESH_FILE = os.path.join("..", "movies.csv")


def tmdb_get(endpoint, params=None):

    if params is None:
        params = {}

    params["api_key"] = API_KEY

    response = requests.get(
        BASE_URL + endpoint,
        params=params,
        timeout=30
    )

    if response.status_code != 200:
        print("TMDB ERROR:", response.status_code)
        return None

    return response.json()


def normalize(text):

    return "".join(
        c.lower()
        for c in text
        if c.isalnum()
    )


def extract_year(url):

    parts = url.rstrip("/").split("-")

    if parts and parts[-1].isdigit():
        return parts[-1]

    return ""


def find_tmdb_movie(title, year):

    params = {
        "query": title,
        "language": "en-US"
    }

    if year:
        params["year"] = year

    search = tmdb_get(
        "/search/movie",
        params
    )

    if not search:
        return None

    results = search.get("results", [])

    if not results:
        return None

    # Exact title + year
    for movie in results:

        tmdb_title = movie.get("title", "")
        release_date = movie.get("release_date", "")

        tmdb_year = release_date[:4] if release_date else ""

        if (
            normalize(tmdb_title) == normalize(title)
            and year
            and tmdb_year == year
        ):
            return movie

    # Exact title
    for movie in results:

        if normalize(movie.get("title", "")) == normalize(title):
            return movie

    # First result as fallback
    return results[0]


def get_movie_details(tmdb_id):

    return tmdb_get(
        f"/movie/{tmdb_id}",
        {
            "language": "en-US",
            "append_to_response": "credits"
        }
    )


def get_director(details):

    for person in details.get("credits", {}).get("crew", []):

        if person.get("job") == "Director":
            return person.get("name", "")

    return ""


def get_cast(details):

    cast = []

    for person in details.get("credits", {}).get("cast", [])[:10]:

        name = person.get("name", "")
        character = person.get("character", "")

        if not name:
            continue

        if character:
            cast.append(f"{name} as {character}")
        else:
            cast.append(name)

    return " | ".join(cast)


print()
print("=" * 60)
print("MOVIEHUB AUTOMATIC UPDATE")
print("=" * 60)
print()

# --------------------------------------------------
# STEP 1: Run Cinejoy scraper
# --------------------------------------------------

print("STEP 1: Getting fresh movies from Cinejoy...")
print()

scraper_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "cinejoy_scraper.py"
)

try:

    result = subprocess.run(
        ["py", scraper_path],
        capture_output=True,
        text=True
    )

    print(result.stdout)

    if result.returncode != 0:
        print("Cinejoy scraper failed.")
        print(result.stderr)
        raise SystemExit

except Exception as e:

    print("Could not run Cinejoy scraper.")
    print(e)
    raise SystemExit


# --------------------------------------------------
# STEP 2: Load existing master database
# --------------------------------------------------

if not os.path.exists(MASTER_FILE):

    print("Master database not found:")
    print(MASTER_FILE)
    raise SystemExit


with open(
    MASTER_FILE,
    "r",
    encoding="utf-8-sig"
) as file:

    existing_movies = list(
        csv.DictReader(file)
    )


existing_urls = {
    movie["url"]
    for movie in existing_movies
}


# --------------------------------------------------
# STEP 3: Load fresh Cinejoy movies
# --------------------------------------------------

if not os.path.exists(FRESH_FILE):

    print("Fresh Cinejoy CSV not found.")
    raise SystemExit


with open(
    FRESH_FILE,
    "r",
    encoding="utf-8-sig"
) as file:

    fresh_movies = list(
        csv.DictReader(file)
    )


new_movies = [
    movie
    for movie in fresh_movies
    if movie["url"] not in existing_urls
]


print()
print("=" * 60)
print("NEW MOVIE CHECK")
print("=" * 60)
print()
print("Existing movies:", len(existing_movies))
print("Fresh Cinejoy movies:", len(fresh_movies))
print("New movies found:", len(new_movies))
print()


if not new_movies:

    print("No new movies found.")
    print("Master database was NOT changed.")
    print()
    raise SystemExit


for movie in new_movies:

    print("NEW:", movie["title"])


# --------------------------------------------------
# STEP 4: Backup master database
# --------------------------------------------------

print()
print("Creating backup...")

shutil.copy2(
    MASTER_FILE,
    BACKUP_FILE
)

print("Backup created:")
print(BACKUP_FILE)


# --------------------------------------------------
# STEP 5: TMDB enrichment
# --------------------------------------------------

print()
print("=" * 60)
print("TMDB ENRICHMENT")
print("=" * 60)
print()

successful = 0
failed = 0


for index, movie in enumerate(new_movies, 1):

    title = movie["title"]
    cinejoy_url = movie["url"]

    print(
        f"[{index}/{len(new_movies)}] {title}"
    )

    year = extract_year(cinejoy_url)

    tmdb_movie = find_tmdb_movie(
        title,
        year
    )

    if not tmdb_movie:

        print("   TMDB NOT FOUND")
        failed += 1
        continue

    tmdb_id = tmdb_movie.get("id")

    details = get_movie_details(
        tmdb_id
    )

    if not details:

        print("   TMDB DETAILS FAILED")
        failed += 1
        continue

    poster_path = details.get(
        "poster_path",
        ""
    )

    poster_url = ""

    if poster_path:
        poster_url = (
            IMAGE_BASE +
            poster_path
        )

    new_record = {
        "title": title,
        "url": cinejoy_url,
        "poster_url": poster_url,
        "release_date": details.get(
            "release_date",
            ""
        ),
        "rating": details.get(
            "vote_average",
            ""
        ),
        "runtime": details.get(
            "runtime",
            ""
        ),
        "certificate": "",
        "director": get_director(details),
        "overview": details.get(
            "overview",
            ""
        ),
        "language": details.get(
            "original_language",
            ""
        ),
        "cast": get_cast(details),
        "tmdb_id": tmdb_id
    }

    existing_movies.append(
        new_record
    )

    successful += 1

    print(
        "   TMDB OK:",
        details.get("title", "")
    )

    print(
        "   TMDB ID:",
        tmdb_id
    )

    time.sleep(0.2)


# --------------------------------------------------
# STEP 6: Save updated master
# --------------------------------------------------

fieldnames = [
    "title",
    "url",
    "poster_url",
    "release_date",
    "rating",
    "runtime",
    "certificate",
    "director",
    "overview",
    "language",
    "cast",
    "tmdb_id"
]


TEMP_FILE = MASTER_FILE + ".tmp"


with open(
    TEMP_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for movie in existing_movies:

        writer.writerow({
            field: movie.get(
                field,
                ""
            )
            for field in fieldnames
        })


os.replace(
    TEMP_FILE,
    MASTER_FILE
)


print()
print("=" * 60)
print("UPDATE COMPLETE")
print("=" * 60)
print()
print("Previous movies:", len(existing_movies) - successful)
print("New movies added:", successful)
print("TMDB failed:", failed)
print("Total movies now:", len(existing_movies))
print()
print("Master:", MASTER_FILE)
print("Backup:", BACKUP_FILE)
print()