from time import time
import json
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import select, Column, func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.config import engine
from app.utilities.utils import GenerateUUID


class BaseCRUD:

    # a function that uses the sqlalchemy select function check if a specific item exists in the database, returning a boolean
    @staticmethod
    async def exists(model, conditions: list) -> bool:
        """ Check if a row exists in the database """
        with Session(engine) as session:
            return session.scalars(
                select(model)
                .exists(*conditions)
            )

    @staticmethod
    def _add_ordering_to_query(model, query, params):
        """ Adds ordering to a query based on the specified field and sort order """
        if "order_by" not in params:
            return query

        model_filter = getattr(model, params["order_by"])
        model_filter = model_filter.desc() if params["sort"] == "DESC" else model_filter.asc()
        return query.order_by(model_filter)

    @staticmethod
    def _filter_query(model, query, params):
        """ Filters a query based on the specified filters """
        if not params.get("filters"):
            return query

        conditions = []
        date_range = {"from_date": "", "to_date": ""}
        for k, v in params["filters"].items():
            if k == "rule_uuid":
                v = json.loads(v)
                or_conditions = or_(*[getattr(model, k) == uuid for uuid in v])
                conditions.append(or_conditions)
            elif k in date_range:
                date_range[k] = v
            elif k == "full_name":
                fuzzy_condition = getattr(model, "full_name").ilike(f"%{v}%")
                conditions.append(fuzzy_condition)
            else:
                conditions.append(getattr(model, k) == v)

        if date_range["from_date"] and date_range["to_date"]:
            conditions.append(getattr(model, "send_on").between(date_range["from_date"], date_range["to_date"]))

        return query.where(*conditions)

    @staticmethod
    async def check_if_exists(model, conditions: list):
        """ Check if a row exists in the database """
        with Session(engine) as session:
            return session.scalars(
                select(model)
                .where(*conditions)
            ).one_or_none()

    @staticmethod
    async def check_if_one_exists(model, conditions: list):
        """ Check if a row exists in the database """
        with Session(engine) as session:
            return session.scalars(
                select(model)
                .where(*conditions)
            ).first()

    @staticmethod
    def get_one(model, conditions: list):
        """ Non-Async method to get one row from the database """
        with Session(engine) as session:
            return session.scalars(
                select(model)
                .where(*conditions)
            ).one_or_none()

    @staticmethod
    async def get_one_where(
        model,
        conditions: list
    ):
        """ Get one row from the database """
        with Session(engine) as session:
            db_item = session.scalars(
                select(model)
                .where(*conditions)
            ).one_or_none()
        return db_item

    @classmethod
    async def get_all(
        cls,
        model,
        params: dict = None,
        pagination: bool = True
    ):
        """ Get all rows from the database for a given model/table """

        with Session(engine) as session:
            query = select(model)
            if params:
                query = cls._add_ordering_to_query(model, query, params)
                query = cls._filter_query(model, query, params)
            if pagination:
                return paginate(session, query)
            return session.scalars(query).all()

    @classmethod
    async def get_all_where(
        cls,
        model,
        conditions: list,
        params: dict = None,
        pagination: bool = True,
        distinct_column: Column = None,
        join_model=None,
        join_condition: list = None
    ):
        """ Get all rows from the database that match the specified conditions """

        with Session(engine) as session:
            if isinstance(model, list):
                if isinstance(join_model, list):
                    query = select(*model).join(join_model[0], join_condition[0]).join(join_model[1], join_condition[1]).where(*conditions)
                    return session.execute(query).fetchall()
                query = select(*model).join(join_model, *join_condition).where(*conditions)
                return session.execute(query).fetchall()
            else:
                query = select(model).where(*conditions)
            if distinct_column is not None:
                query = select(distinct_column).distinct().where(*conditions)
            if params:
                query = cls._add_ordering_to_query(model, query, params)
                query = cls._filter_query(model, query, params)

            if pagination:
                return paginate(session, query)
            return session.scalars(query).all()

    @classmethod
    async def get_all_in(
        cls,
        model,
        field,
        field_data: list,
        params: dict = None,
        pagination: bool = False
    ):
        """ Get all rows from the database that match the specified conditions """

        with Session(engine) as session:
            query = select(model).where(field.in_(field_data))
            if params:
                query = cls._add_ordering_to_query(model, query, params)
                query = cls._filter_query(model, query, params)

            if pagination:
                return paginate(session, query)
            return session.scalars(query).all()

    @staticmethod
    async def get_row_count(
        model,
        conditions
    ):
        with Session(engine) as session:
            count = session.query(func.count(model.uuid)).filter(*conditions).scalar()  # pylint: disable=not-callable
            return count

    @staticmethod
    async def create(model_objs):
        """ Create one or more rows in the database for the specified model """
        with Session(engine) as session:
            model_objs = model_objs if (is_list := isinstance(model_objs, list)) else [model_objs]

            for obj in model_objs:
                obj.uuid = GenerateUUID.hex() if not obj.uuid else obj.uuid
                obj.time_created = obj.time_updated = obj.time_last_seen = int(time())

            session.add_all(model_objs)
            session.commit()

            for obj in model_objs:
                session.refresh(obj)

            return model_objs if is_list else model_objs[0]

    @staticmethod
    async def seed_database(model_objs):
        """ Create one or more rows in the database for the specified model """
        model_objs = model_objs if (is_list := isinstance(model_objs, list)) else [model_objs]

        for obj in model_objs:
            try:
                with Session(engine, expire_on_commit=False) as session:
                    existing_obj = session.query(obj.__class__).filter_by(uuid=obj.uuid).first()
                    if existing_obj is not None:
                        continue  # Skip this object because it already exists in the database

                    obj.uuid = GenerateUUID.hex() if not obj.uuid else obj.uuid
                    obj.time_created = obj.time_updated = int(time())

                    session.add(obj)
                    session.commit()
            except IntegrityError:
                pass

        return model_objs if is_list else model_objs[0]

    @staticmethod
    async def update(model, conditions: list, updates_obj):
        """ Update a row in the database for the specified model """
        with Session(engine) as session:
            db_item = session.scalars(
                select(model)
                .where(*conditions)
            ).one_or_none()

            if db_item is None:
                raise ValueError(f"Update: No {model.__name__} found with the specified conditions")

            updated_fields = updates_obj.dict(exclude_unset=True, exclude_none=True).items()
            for key, value in updated_fields:
                setattr(db_item, key, value)
            db_item.time_updated = int(time())

            session.add(db_item)
            session.commit()
            session.refresh(db_item)
            return db_item

    @staticmethod
    async def bulk_update(model, conditions: list, updates_objs, key_list: list):
        """ Update multiple rows in the database for the specified model """
        with Session(engine) as session:
            # create an empty list for the later to be updated items
            updates = []
            # get each item from the database filtering by the uuids in the key_list
            db_items = session.query(model).where(*conditions).filter(model.uuid.in_(key_list)).all()
            # creating a dictionary of the items from the database
            items = {}
            # creating an empty list for the items that were not updated
            not_updated = []
            for db_item in db_items:
                # adding each item to the dictionary with the uuid as the key
                items[db_item.uuid] = db_item
            for obj in updates_objs:
                if obj.uuid not in items:
                    not_updated.append(obj)
                    continue
                item_from_db = items[obj.uuid]
                update_fields = obj.dict(exclude_unset=True, exclude_none=True).items()
                for key, value in update_fields:
                    setattr(item_from_db, key, value)
                    item_from_db.time_updated = int(time())
                updates.append(item_from_db)

            session.add_all(updates)
            session.commit()
            for i in updates:
                session.refresh(i)
            return {"updated": updates, "not_updated": not_updated}

    @classmethod
    async def update_without_lookup(cls, item, commit: bool = False):
        """ Committing a change to an item that has been previously looked up and modified inside its respective Model Action file """
        with Session(engine) as session:
            if isinstance(item, list):
                for i in item:
                    i.time_updated = int(time())
                    session.add(i)
                session.commit()
                for i in item:
                    session.refresh(i)
            else:
                item.time_updated = int(time())
                session.add(item)
                session.commit()
                session.refresh(item)
            return item

    @classmethod
    async def migrate(cls, list_of_models, list_of_conditions, updates_obj):
        """Updates the same column/columns in a row for the given models"""
        with Session(engine) as session:
            try:
                for model, conditions in zip(list_of_models, list_of_conditions):
                    db_items = session.scalars(
                        select(model)
                        .where(*conditions)
                    ).all()

                    if not db_items:
                        continue

                    for db_item in db_items:
                        updated_fields = updates_obj.dict(exclude_unset=True, exclude_none=True).items()
                        for key, value in updated_fields:
                            setattr(db_item, key, value)
                        db_item.time_updated = int(time())

                        session.add(db_item)
                session.commit()
            except Exception:
                return False
            return True

    @staticmethod
    def non_async_delete_one(model, conditions: list):
        """ Delete a row from the database for the specified model """
        with Session(engine) as session:
            db_item = session.scalars(
                select(model)
                .where(*conditions)
            ).one_or_none()

            try:
                session.delete(db_item)
                session.commit()
                return {"ok": True, "Deleted": db_item}
            except Exception:
                return {"ok": False, "Not Deleted": db_item}

    @staticmethod
    async def delete_one(model, conditions: list):
        """ Delete a row from the database for the specified model """
        with Session(engine) as session:
            db_item = session.scalars(
                select(model)
                .where(*conditions)
            ).one_or_none()

            try:
                session.delete(db_item)
                session.commit()
                return {"ok": True, "Deleted": db_item}
            except Exception:
                return {"ok": False, "Not Deleted": db_item}

    @staticmethod
    async def delete_all(model, conditions: list):
        """ Delete all rows from the database for the specified model """
        with Session(engine) as session:
            db_items = session.scalars(
                select(model)
                .where(*conditions)
            ).all()

            results = []
            for item in db_items:
                try:
                    session.delete(item)
                    results.append({"ok": True, "Deleted": db_items})
                except Exception:
                    results.append({"ok": False, "Not Deleted": db_items})
            session.commit()
            return results

    @staticmethod
    async def delete_without_lookup(item):
        """ Deleting an item that has been previously looked up and processed inside its respective Model Action file """
        with Session(engine) as session:
            try:
                session.delete(item)
                session.commit()
                return {"ok": True, "Deleted": item}
            except Exception:
                return {"ok": False, "Not Deleted": item}

    # TODO
    # def GetManyByIds(self, table, fields, field, ids=None, orderby=None, orderby_dir='DESC', joiner='and'):
    # async def get_all_wherein(model, field, ids: list, order_by=None, sort='DESC'):
    #   '''
    #   Get all rows from the database
    #   :param model(DataModel): model/table to query
    #   :param conditions(tuple): conditions to match
    #   :param order_by(None|str): the field to sort
    #   :param model(None): model/table to query
    #   :return: returns [model(DataModel),...]
    #   '''
    #   with Session(engine) as session:
    #       query = select(model).where(*conditions)
    #       query = BaseCRUD._update_query_with_ordering_params(model, query, order_by, sort)
    #       return session.scalars(query).all()
