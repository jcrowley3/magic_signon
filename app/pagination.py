from fastapi_pagination.links import Page
from pydantic import Field

Page = Page.with_custom_options(
    size=Field(10, ge=1, le=100), # default 10 per page, min 1, max 100
    page=Field(1, ge=1) # because page 0 is not a thing (this comment brought to you by GitHub Copilot)
)
