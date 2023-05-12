import os
import logging
import pathlib
from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import hashlib
import os
import sqlite3


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


def convertItemList2Json(list):
    res = {"items": []}
    for (category, name, filename) in list:
        res["items"].append(
            {"name": name, "category": category, "image_filename": filename})
    return res


def getItems():
    try:
        con = sqlite3.connect("../db/mercari.sqlite3")
        cur = con.cursor()
        cur.execute(
            """SELECT categories.name, items.name, items.image_name FROM items 
                JOIN categories ON items.category_id = categories.id;""")
        return convertItemList2Json(cur.fetchall())
    except sqlite3.Error as err:
        logger.debug(err)
        return {}


def getItemsById(id):
    try:
        con = sqlite3.connect("../db/mercari.sqlite3")
        cur = con.cursor()
        cur.execute(
            """SELECT categories.name, items.name, items.image_name FROM items 
                    JOIN categories ON items.category_id = categories.id WHERE items.id = ?;""", id)
        return convertItemList2Json(cur.fetchall())
    except sqlite3.Error as err:
        logger.debug(err)
        return {}


def saveItems(name, category, filename):
    try:
        con = sqlite3.connect("../db/mercari.sqlite3")
        cur = con.cursor()
        cur.execute("""SELECT id from categories where name = ?""", (category,))
        category_id = -1
        res = cur.fetchall()
        if len(res) >= 1:
            category_id = res[0][0]
        else:
            cur.execute(
                """INSERT INTO categories (name) VALUES(?) RETURNING id;""", (category,))
            category_id = cur.fetchall()[0][0]
        cur.execute(
            """INSERT INTO items (name, category_id, image_name) VALUES(?,?,?);""",
            (name, category_id, filename,))
        con.commit()
    except sqlite3.Error as err:
        logger.debug(err)
        return {}


def searchItems(keyword):
    try:
        con = sqlite3.connect("../db/mercari.sqlite3")
        cur = con.cursor()
        cur.execute(
            """SELECT categories.name, items.name, items.image_name FROM items 
                    JOIN categories ON items.category_id = categories.id
                    WHERE items.name LIKE ?""", (f'%{keyword}%',))
        return convertItemList2Json(cur.fetchall())
    except sqlite3.Error as err:
        logger.debug(err)
        return {}


def saveFile(image: UploadFile):
    extension = os.path.splitext(
        image.filename)[-1] if image.filename else '.png'
    content = image.file.read()
    sha256 = hashlib.sha256(content)
    with open(f'images/{sha256.hexdigest()}{extension}', 'w+b') as outfile:
        outfile.write(content)
        outfile.close()
    return sha256.hexdigest()


@ app.get("/")
def root():
    return {"message": "Hello, world!"}


@ app.get("/items")
def get_items():
    return getItems()


@ app.get("/search")
def search_items(keyword: str = Form(...)):
    return searchItems(keyword)


@ app.post("/items")
def add_item(name: str = Form(...), category: str = Form(...), image: UploadFile = Form(...)):
    logger.info(f"Receive item: {name} {category}")
    filename = saveFile(image)
    saveItems(name, category, filename)
    return {"message": f"item received: {name}"}


@ app.get("/items/{item_id}")
async def get_item(item_id):
    return getItemsById(item_id)


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
