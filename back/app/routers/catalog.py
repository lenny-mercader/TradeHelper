"""Browsing the full US catalog plus already-opened international instruments. Public."""

from typing import Annotated, Literal

from fastapi import APIRouter, Query

from app.routers.deps import SessionDep
from app.schemas import CatalogFacets, CatalogPage, CatalogRow
from app.services import catalog_browse

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("")
def get_catalog(
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=64)] = None,
    country: Annotated[list[str] | None, Query()] = None,
    sector: Annotated[str | None, Query()] = None,
    min_change: Annotated[float | None, Query()] = None,
    max_change: Annotated[float | None, Query()] = None,
    sort: Annotated[Literal["change", "market_cap", "name"], Query()] = "market_cap",
    order: Annotated[Literal["asc", "desc"], Query()] = "desc",
    page: Annotated[int, Query(ge=1)] = 1,
) -> CatalogPage:
    result = catalog_browse.search(
        session,
        q=q,
        countries=country,
        sector=sector,
        min_change=min_change,
        max_change=max_change,
        sort=sort,
        descending=order == "desc",
        page=page,
    )
    return CatalogPage(
        rows=[CatalogRow(**vars(r)) for r in result.rows],
        total=result.total,
        page=page,
        page_size=catalog_browse.PAGE_SIZE,
    )


@router.get("/facets")
def get_facets(session: SessionDep) -> CatalogFacets:
    """Countries/sectors actually present, to build the filter checkboxes from real data."""
    return CatalogFacets(**catalog_browse.facets(session))
