import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib
from pathlib import Path
from db import SqliteItemsRepository


app = FastAPI()
db = SqliteItemsRepository()
logger = logging.getLogger("uvicorn")
logger.level = logging.DEBUG
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [os.environ.get('FRONT_URL', 'http://localhost:3000')]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


def save_file(image: UploadFile) -> str:
    extension = Path(image.filename).suffix if image.filename else '.png'
    content = image.file.read()
    sha256 = hashlib.sha256(content)
    Path(f'images/{sha256.hexdigest()}{extension}').write_bytes(content)
    return sha256.hexdigest()


@ app.get("/")
def root():
    return {"message": "Hello, world!"}


@ app.get("/items")
def get_items():
    return db.get_items()


@ app.get("/search")
def search_items(keyword: str = Form(...)):
    return db.search_items_by_name(keyword)


@ app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = Form(...)):
    logger.info(f"Receive item: {name} {category}")
    filename = save_file(image)
    db.add_items(name, category, filename)
    return {"message": f"item received: {name}"}


@ app.get("/items/{item_id}")
async def get_item(item_id):
    return db.get_item_by_id(item_id)


@ app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(
            status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)
