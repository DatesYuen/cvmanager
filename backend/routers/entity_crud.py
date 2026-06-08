"""Generic CRUD router factory for all entity types (papers, projects, patents, etc.)."""
from typing import List, Optional, Type
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.database import get_db, Base
from backend.models import User, Person
from backend.services.auth_service import get_current_user
from backend.services.paper_service import derive_paper_role_flags, enrich_paper_data


ENTITY_REGISTRY = {}
DEFAULT_LIST_PAGE_SIZE = 1000
MAX_LIST_PAGE_SIZE = 5000


def register_entity(name: str, model: Type[Base], out_schema, create_schema, update_schema,
                    list_filter_fields: list = None):
    ENTITY_REGISTRY[name] = {
        "model": model,
        "out": out_schema,
        "create": create_schema,
        "update": update_schema,
        "filter_fields": list_filter_fields or [],
    }


def create_entity_router(entity_name: str) -> APIRouter:
    info = ENTITY_REGISTRY[entity_name]
    Model = info["model"]
    OutSchema = info["out"]
    CreateSchema = info["create"]
    UpdateSchema = info["update"]

    router = APIRouter(prefix=f"/api/{entity_name}", tags=[entity_name])

    @router.get("/", response_model=List[OutSchema])
    def list_items(person_id: Optional[int] = None,
                   review_status: Optional[str] = None,
                   page: int = Query(1, ge=1),
                   page_size: int = Query(DEFAULT_LIST_PAGE_SIZE, ge=1, le=MAX_LIST_PAGE_SIZE),
                   db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
        q = db.query(Model)
        if person_id is not None:
            q = q.filter(Model.person_id == person_id)
        if review_status and hasattr(Model, "review_status"):
            q = q.filter(Model.review_status == review_status)
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return items

    @router.get("/filter-fields")
    def get_filter_fields(user: User = Depends(get_current_user)):
        """Return available filter fields for this entity type."""
        columns = [c.name for c in Model.__table__.columns
                   if c.name not in ("id", "raw_text", "confidence", "review_status", "person_id")]
        return columns

    @router.get("/{item_id}", response_model=OutSchema)
    def get_item(item_id: int, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
        item = db.query(Model).get(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        return item

    @router.post("/", response_model=OutSchema)
    def create_item(data: CreateSchema, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
        item_data = data.model_dump()
        # Handle nested relationships
        authors = item_data.pop("authors", None)
        applicants = item_data.pop("applicants", None)
        if authors is not None and hasattr(Model, "authors") and item_data.get("person_id"):
            person = db.query(Person).get(item_data["person_id"])
            if person:
                item_data.update(derive_paper_role_flags(authors, person.name, person.name_en))
            item_data.update(enrich_paper_data(db, {**item_data, "authors": authors}, fetch_external=True))
        item = Model(**item_data)
        db.add(item)
        db.flush()

        if authors is not None and hasattr(Model, "authors"):
            from backend.models.paper import PaperAuthor
            for a in authors:
                db.add(PaperAuthor(paper_id=item.id, **a))

        if applicants is not None and hasattr(Model, "applicants"):
            from backend.models.patent import PatentApplicant
            for a in applicants:
                db.add(PatentApplicant(patent_id=item.id, **a))

        db.commit()
        db.refresh(item)
        return item

    @router.put("/{item_id}", response_model=OutSchema)
    def update_item(item_id: int, data: UpdateSchema, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
        item = db.query(Model).get(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        update_data = data.model_dump(exclude_unset=True)

        authors = update_data.pop("authors", None)
        applicants = update_data.pop("applicants", None)

        for field, value in update_data.items():
            setattr(item, field, value)

        if authors is not None and hasattr(item, "authors"):
            from backend.models.paper import PaperAuthor
            for a in item.authors:
                db.delete(a)
            for a in authors:
                db.add(PaperAuthor(paper_id=item.id, **a))
            role_flags = derive_paper_role_flags(authors, item.person.name, getattr(item.person, "name_en", ""))
            item.is_first_author = role_flags["is_first_author"]
            item.is_corresponding_author = role_flags["is_corresponding_author"]

        if hasattr(Model, "authors"):
            enriched = enrich_paper_data(
                db,
                {c.name: getattr(item, c.name) for c in Model.__table__.columns if c.name != "id"},
                fetch_external=any(field in update_data for field in ("title", "journal", "doi")),
            )
            for field, value in enriched.items():
                if hasattr(item, field) and field not in {"id", "person_id"}:
                    setattr(item, field, value)

        if applicants is not None and hasattr(item, "applicants"):
            from backend.models.patent import PatentApplicant
            for a in item.applicants:
                db.delete(a)
            for a in applicants:
                db.add(PatentApplicant(patent_id=item.id, **a))

        db.commit()
        db.refresh(item)
        return item

    @router.delete("/{item_id}")
    def delete_item(item_id: int, db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
        item = db.query(Model).get(item_id)
        if not item:
            raise HTTPException(status_code=404, detail=f"{entity_name} not found")
        db.delete(item)
        db.commit()
        return {"msg": f"{entity_name} deleted"}

    return router
