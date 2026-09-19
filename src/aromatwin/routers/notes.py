from fastapi import APIRouter, Depends
from pydantic import BaseModel

from aromatwin.security import require_private_api_key


class NoteRead(BaseModel):
    id: int
    name: str
    slug: str
    note_type: str


class AccordRead(BaseModel):
    id: int
    name: str
    slug: str


router = APIRouter(tags=["taxonomy"], dependencies=[Depends(require_private_api_key)])


@router.get("/notes", response_model=list[NoteRead])
def notes() -> list[NoteRead]:
    return []


@router.get("/accords", response_model=list[AccordRead])
def accords() -> list[AccordRead]:
    return []
