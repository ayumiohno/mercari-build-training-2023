import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import hashlib
import os

app = FastAPI()
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


def getItems():
    try:
        with open('./item.json', mode='r', encoding="utf-8") as f:
            return json.load(f, strict=False)
    except json.decoder.JSONDecodeError:  # json形式でない場合
        return {}
    except FileNotFoundError:  # ファイルがない場合
        return {}


def saveItems(name, category, filename):
    try:
        with open('./item.json', mode='r', encoding="utf-8") as f:
            data = json.load(f, strict=False)
    except json.decoder.JSONDecodeError:  # json形式でない場合
        data = {"items": []}
    except FileNotFoundError:  # ファイルがない場合
        data = {"items": []}
    with open('./item.json', mode='w', encoding="utf-8") as f:
        data["items"].append(
            {"name": name, "category": category, "image_filename": filename})
        json.dump(data, f)


def saveFile(image: UploadFile):
    extension = os.path.splitext(
        image.filename)[-1] if image.filename else '.png'
    content = image.file.read()
    sha256 = hashlib.sha256(content)
    with open(f'images/{sha256.hexdigest()}{extension}', 'w+b') as outfile:
        outfile.write(content)
        outfile.close()
    return sha256.hexdigest()


@app.get("/")
def root():
    return {"message": "Hello, world!"}


@app.get("/items")
def get_items():
    return getItems()


@app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = Form(...)):
    logger.info(f"Receive item: {name} {category}")
    filename = saveFile(image)
    saveItems(name, category, filename)
    return {"message": f"item received: {name}"}


@app.get("/items/{item_id}")
async def get_item(item_id):
    try:
        with open('./item.json', mode='r', encoding="utf-8") as f:
            item_id = int(item_id)
            data = json.load(f, strict=False)
            if (len(data["items"]) < item_id or item_id < 0):  # indexが範囲外のとき
                logger.debug(f"Item not found: {item_id}")
                return {"message": "Item Not found"}
            return data["items"][item_id - 1]
    except ValueError as err:
        logger.debug(err)
        return {"message": "Error"}


@app.get("/image/{image_filename}")
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
