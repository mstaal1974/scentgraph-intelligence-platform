from fastapi import APIRouter

from scentgraph.schemas.note import AccordRead, NoteRead

router = APIRouter(tags=["taxonomy"])


@router.get("/notes", response_model=list[NoteRead])
def notes() -> list[NoteRead]:
    return [NoteRead(id=1, name="Bergamot", slug="bergamot", note_type="top")]


@router.get("/accords", response_model=list[AccordRead])
def accords() -> list[AccordRead]:
    return [AccordRead(id=1, name="Woody", slug="woody")]
