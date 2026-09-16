from fastapi import APIRouter
from pydantic import BaseModel


class NoteRead(BaseModel):
    id: int
    name: str
    slug: str
    note_type: str


class AccordRead(BaseModel):
    id: int
    name: str
    slug: str


router = APIRouter(tags=["taxonomy"])


@router.get("/notes", response_model=list[NoteRead])
def notes() -> list[NoteRead]:
    return []


@router.get("/accords", response_model=list[AccordRead])
def accords() -> list[AccordRead]:
    return []
