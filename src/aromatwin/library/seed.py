"""Deterministic construction of the first-party profile library seed.

The seed is a designed matrix rather than a random generator: eight coherent scent directions,
each with a perfumery-plausible note pyramid and reviewed taxonomy, distributed across twelve
fictional houses. Note names are generic perfumery ingredients, not third-party content.
"""

from __future__ import annotations

from dataclasses import dataclass

PROFILES_PER_HOUSE = 4


@dataclass(frozen=True)
class Direction:
    key: str
    family: str
    notes: tuple[str, ...]
    accords: tuple[str, ...]
    mood: tuple[str, ...]
    occasion: tuple[str, ...]
    season: tuple[str, ...]
    concentration: str
    names: tuple[str, ...]
    motif: str
    # One signature pair per name: an extra note and an extra accord. Without this every
    # profile in a direction would share a vector, and ranking inside a direction would be
    # arbitrary. A real library gets this variation from each composition.
    variants: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class SeedProfile:
    ordinal: int
    house: str
    house_ordinal: int
    name: str
    direction: Direction
    description: str
    signature_note: str
    signature_accord: str

    @property
    def notes(self) -> tuple[str, ...]:
        return (*self.direction.notes, self.signature_note)

    @property
    def accords(self) -> tuple[str, ...]:
        extra = () if self.signature_accord in self.direction.accords else (self.signature_accord,)
        return (*self.direction.accords, *extra)


# Direction 0 is the woody chypre so the library's first record stays Aster & Vale "Moonlit
# Grove", the identity earlier samples and documentation already reference.
DIRECTIONS: tuple[Direction, ...] = (
    Direction(
        key="woody_chypre",
        family="woody chypre",
        notes=("bergamot", "iris", "oakmoss", "patchouli", "cedar", "leather"),
        accords=("woody", "green", "leather"),
        mood=("refined", "grounded"),
        occasion=("work", "evening"),
        season=("autumn", "winter"),
        concentration="Eau de parfum",
        names=("Moonlit Grove", "Slate Orchard", "Quiet Timber", "Umbra Fern",
               "Ashwood Letter", "Low Meridian"),
        motif="a mossy, cedar-lined calm",
        variants=(
            ("juniper", "aromatic"), ("tobacco leaf", "smoky"), ("wet stone", "green"),
            ("dried fig", "fruity"), ("birch tar", "smoky"), ("grey amber", "amber"),
        ),
    ),
    Direction(
        key="citrus_aromatic",
        family="citrus aromatic",
        notes=("bergamot", "lemon", "neroli", "lavender", "rosemary", "white musk"),
        accords=("citrus", "fresh", "aromatic"),
        mood=("bright", "uplifting"),
        occasion=("daytime", "casual"),
        season=("spring", "summer"),
        concentration="Eau de toilette",
        names=("Citrine Hour", "First Terrace", "Lemon Ledger", "Bright Latitude",
               "Neroli Post", "Morning Rind"),
        motif="a sunlit citrus opening over clean herbs",
        variants=(
            ("grapefruit", "fruity"), ("green tea", "green"), ("mandarin", "sweet"),
            ("basil", "green"), ("petitgrain", "aromatic"), ("ginger", "spicy"),
        ),
    ),
    Direction(
        key="fresh_aquatic",
        family="fresh aquatic",
        notes=("sea salt", "bergamot", "melon", "water lily", "driftwood", "ambergris"),
        accords=("aquatic", "marine", "fresh"),
        mood=("clean", "energising"),
        occasion=("daytime", "casual"),
        season=("spring", "summer"),
        concentration="Eau de toilette",
        names=("Saltline", "Harbour Glass", "Tidewater Room", "Cold Swim",
               "Driftwood Signal", "Open Water"),
        motif="a saline, open-air brightness",
        variants=(
            ("cucumber", "green"), ("mineral salt", "marine"), ("green mango", "fruity"),
            ("juniper", "aromatic"), ("blue lotus", "floral"), ("grey musk", "musky"),
        ),
    ),
    Direction(
        key="green_fougere",
        family="aromatic fougere",
        notes=("galbanum", "lavender", "geranium", "oakmoss", "vetiver", "tonka bean"),
        accords=("green", "aromatic", "woody"),
        mood=("crisp", "composed"),
        occasion=("daytime", "work"),
        season=("spring", "autumn"),
        concentration="Eau de parfum",
        names=("Green Ledger", "Fern Protocol", "Cut Stems", "Herb Quarter",
               "Vetiver Study", "Clean Field"),
        motif="a crisp green fougere structure",
        variants=(
            ("clary sage", "aromatic"), ("fig leaf", "fruity"), ("mint", "fresh"),
            ("angelica", "green"), ("hay", "powdery"), ("coumarin", "sweet"),
        ),
    ),
    Direction(
        key="white_floral",
        family="white floral",
        notes=("jasmine", "tuberose", "orange blossom", "ylang ylang", "sandalwood", "musk"),
        accords=("floral", "sweet", "powdery"),
        mood=("romantic", "luminous"),
        occasion=("evening", "special occasion"),
        season=("spring", "summer"),
        concentration="Eau de parfum",
        names=("White Register", "Tuberose Wing", "Night Blossom", "Petal Archive",
               "Jasmine Hour", "Lantern Bloom"),
        motif="a luminous white-floral heart",
        variants=(
            ("gardenia", "green"), ("honeysuckle", "sweet"), ("magnolia", "citrus"),
            ("heliotrope", "powdery"), ("beeswax", "gourmand"), ("white amber", "amber"),
        ),
    ),
    Direction(
        key="rose_amber",
        family="amber floral",
        notes=("rose", "saffron", "raspberry", "patchouli", "labdanum", "vanilla"),
        accords=("floral", "amber", "spicy"),
        mood=("opulent", "warm"),
        occasion=("evening", "special occasion"),
        season=("autumn", "winter"),
        concentration="Extrait de parfum",
        names=("Rose Meridian", "Saffron Letter", "Crimson Register", "Velvet Ledger",
               "Amber Rose Study", "Deep Bloom"),
        motif="a saffron-lit rose over warm resins",
        variants=(
            ("oud", "woody"), ("blackcurrant", "fruity"), ("clove", "spicy"),
            ("myrrh", "resinous"), ("praline", "gourmand"), ("iris", "powdery"),
        ),
    ),
    Direction(
        key="amber_oud",
        family="amber woody",
        notes=("oud", "incense", "saffron", "rose", "labdanum", "sandalwood"),
        accords=("amber", "woody", "smoky", "resinous"),
        mood=("opulent", "nocturnal"),
        occasion=("evening", "special occasion"),
        season=("autumn", "winter"),
        concentration="Extrait de parfum",
        names=("Night Resin", "Smoke Meridian", "Oud Protocol", "Censer Room",
               "Dark Latitude", "Ember Register"),
        motif="a smoky resinous depth",
        variants=(
            ("leather", "leather"), ("cypriol", "smoky"), ("dried plum", "fruity"),
            ("tonka bean", "sweet"), ("frankincense", "resinous"), ("black pepper", "spicy"),
        ),
    ),
    Direction(
        key="gourmand_vanilla",
        family="gourmand",
        notes=("vanilla", "tonka bean", "caramel", "coffee", "benzoin", "musk"),
        accords=("sweet", "gourmand", "warm"),
        mood=("comforting", "indulgent"),
        occasion=("evening", "casual"),
        season=("autumn", "winter"),
        concentration="Eau de parfum",
        names=("Sugar Ledger", "Warm Pantry", "Vanilla Quarter", "Late Caramel",
               "Coffee Room", "Soft Confection"),
        motif="a warm, edible sweetness",
        variants=(
            ("dark chocolate", "dark"), ("toasted hazelnut", "woody"), ("rum", "fruity"),
            ("cinnamon", "spicy"), ("milk", "powdery"), ("salted butter", "musky"),
        ),
    ),
)

HOUSES: tuple[str, ...] = (
    "Aster & Vale",
    "Cormorant Hall",
    "Solene Atelier",
    "Meridian & Ash",
    "Halcyon Rue",
    "Verdigris House",
    "Lumen Botanica",
    "Ferrier & Cole",
    "Saltwood Parfums",
    "Ombra Fiore",
    "Northwind Apothecary",
    "Calder & Wren",
)

_SHAPES = (
    "An original AromaTwin profile for {house}, built around {motif}. The composition moves from "
    "{top} through {heart} to a base of {base}.",
    "{house} works {motif} into a {family} reading. {Top} open the profile, {heart} carry its "
    "centre, and {base} close it.",
    "A {family} direction from {house} shaped by {motif}. The profile is drawn with {top} at the "
    "top, {heart} at the heart, and {base} in the base.",
)


def _phrase(values: tuple[str, ...]) -> str:
    if len(values) == 1:
        return values[0]
    return f"{', '.join(values[:-1])} and {values[-1]}"


def _describe(house: str, direction: Direction, ordinal: int, signature: str) -> str:
    """Return original copy composed from the reviewed taxonomy, never third-party text."""
    top = _phrase(direction.notes[:2])
    body = _SHAPES[ordinal % len(_SHAPES)].format(
        house=house,
        motif=direction.motif,
        family=direction.family,
        top=top,
        Top=top[0].upper() + top[1:],
        heart=_phrase(direction.notes[2:4]),
        base=_phrase(direction.notes[4:]),
    )
    return f"{body} A thread of {signature} separates it from others in the same direction."


def build_seed_profiles() -> list[SeedProfile]:
    """Return the full library seed, deterministic in content and ordering."""
    used: dict[str, int] = {}
    profiles: list[SeedProfile] = []
    for house_index, house in enumerate(HOUSES):
        for slot in range(PROFILES_PER_HOUSE):
            # Rotating the starting direction per house spreads every direction evenly across
            # the library while giving each house four distinct directions.
            direction = DIRECTIONS[(house_index * 3 + slot * 2) % len(DIRECTIONS)]
            name_index = used.get(direction.key, 0)
            used[direction.key] = name_index + 1
            ordinal = len(profiles)
            note, accord = direction.variants[name_index % len(direction.variants)]
            profiles.append(
                SeedProfile(
                    ordinal=ordinal,
                    house=house,
                    house_ordinal=house_index + 1,
                    name=direction.names[name_index % len(direction.names)],
                    direction=direction,
                    description=_describe(house, direction, ordinal, note),
                    signature_note=note,
                    signature_accord=accord,
                )
            )
    return profiles
