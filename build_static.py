import os
import shutil
from app import app

OUTPUT = "netlify"

if os.path.exists(OUTPUT):
    shutil.rmtree(OUTPUT)

os.makedirs(OUTPUT)

client = app.test_client()

response = client.get("/")
open(f"{OUTPUT}/index.html", "wb").write(response.data)

print("Static build created.")
