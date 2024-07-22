import os
from enum import Enum
from typing import Optional
from fastapi import Query, Request, Header


class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

    def __str__(self):
        return self.value


def query_params(
    request: Request,
    order_by: Optional[str] = "uuid",
    sort: SortOrder = Query(default=SortOrder.DESC),
    expand: Optional[bool] = False
):
    params = {
        "order_by": order_by,
        "sort": str(sort),
        "expand": expand,
        "filters": {},
        "page": None,
        "size": None
    }
    for param in request.query_params._dict:
        if param not in params["filters"] and param not in params:
            params["filters"].update({param: request.query_params._dict.get(param)})
    return params


def get_token(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer"):
        return authorization.split(" ")[1]


def test_mode():
    pm = os.environ.get("ENV")
    pytest = os.environ.get("TEST_MODE", False)
    if pm != "local" and not pytest:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="No tests running")
    else:
        return True
