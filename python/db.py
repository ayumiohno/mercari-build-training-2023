import logging
import sqlite3
import json
from abc import ABCMeta, abstractmethod

from pydantic.types import OptionalInt

logger = logging.getLogger("uvicorn")
logger.level = logging.DEBUG

db_path = "mercari.sqlite3"


class CategoriesRepository(metaclass=ABCMeta):
    @abstractmethod
    def get_id_by_name(self, name) -> OptionalInt:
        pass

    @abstractmethod
    def add_category(self, name) -> OptionalInt:
        pass


class ItemsRepository(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def get_items(self) -> dict:
        pass

    @abstractmethod
    def get_item_by_id(self, id) -> dict:
        pass

    @abstractmethod
    def add_items(self, name, category, filename) -> dict:
        pass

    @abstractmethod
    def search_items_by_name(self, name) -> dict:
        pass


class SqliteCategoriesRepository(CategoriesRepository):
    def get_id_by_name(self, name) -> OptionalInt:
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(
                """SELECT id from categories where name = ?""", (name,))
            res = cur.fetchall()
            con.close()
            if len(res) > 0:
                return res[0][0]
            else:
                return None
        except sqlite3.Error as err:
            logger.debug(err)
            return None

    def add_category(self, name) -> OptionalInt:
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(
                """INSERT INTO categories (name) VALUES(?) RETURNING id;""", (name,))
            con.commit()
            con.close()
            return cur.fetchall()[0][0]
        except sqlite3.Error as err:
            logger.debug(err)
            return None


class SqliteItemsRepository(ItemsRepository):
    def __init__(self):
        pass

    def __convert_item_list_to_dict(self, list):
        res = {"items": []}
        for (category, name, filename) in list:
            res["items"].append(
                {"name": name, "category": category, "image_filename": filename})
        return res

    def get_items(self) -> dict:
        try:
            print("called")
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(
                """SELECT categories.name, items.name, items.image_name FROM items
                JOIN categories ON items.category_id = categories.id;""")
            res = self.__convert_item_list_to_dict(cur.fetchall())
            con.close()
            return res
        except sqlite3.Error as err:
            logger.debug(err)
            return {}

    def get_item_by_id(self, id) -> dict:
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(
                """SELECT categories.name, items.name, items.image_name FROM items
                    JOIN categories ON items.category_id = categories.id WHERE items.id = ?;""", id)
            res = self.__convert_item_list_to_dict(cur.fetchall())
            con.close()
            return res
        except sqlite3.Error as err:
            logger.debug(err)
            return {}

    def add_items(self, name, category, filename):
        try:
            categories_repo = SqliteCategoriesRepository()
            category_id = categories_repo.get_id_by_name(category)
            if not category_id:
                category_id = categories_repo.add_category(category)
            if not category_id:
                logger.debug("err")
                return {}
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(
                """INSERT INTO items (name, category_id, image_name) VALUES(?,?,?);""",
                (name, category_id, filename,))
            con.commit()
            con.close()
        except sqlite3.Error as err:
            logger.debug(err)
            return {}

    def search_items_by_name(self, keyword):
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(
                """SELECT categories.name, items.name, items.image_name FROM items
                    JOIN categories ON items.category_id = categories.id
                    WHERE items.name LIKE ?""", (f'%{keyword}%',))
            res = self.__convert_item_list_to_dict(cur.fetchall())
            con.close()
            return res
        except sqlite3.Error as err:
            logger.debug(err)
            return {}


class JsonItemsRepository(ItemsRepository):
    def get_items(self) -> dict:
        try:
            with open('./item.json', mode='r', encoding="utf-8") as f:
                return json.load(f, strict=False)
        except json.decoder.JSONDecodeError:  # json形式でない場合
            return {}
        except FileNotFoundError:  # ファイルがない場合
            return {}

    def add_items(self, name, category, filename):
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

    def get_item_by_id(self, id) -> dict:
        try:
            with open('./item.json', mode='r', encoding="utf-8") as f:
                item_id = int(id)
                data = json.load(f, strict=False)
                if (len(data["items"]) < item_id or item_id < 0):  # indexが範囲外のとき
                    logger.debug(f"Item not found: {item_id}")
                    return {}
                return data["items"][item_id - 1]
        except ValueError as err:
            logger.debug(err)
            return {}

    def search_items_by_name(self, _) -> dict:
        return {}
