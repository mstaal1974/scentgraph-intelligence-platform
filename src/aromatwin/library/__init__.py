"""First-party fragrance profile library seed.

Every profile here is original AromaTwin content describing fictional houses. Nothing is
derived from a third-party fragrance database, and no real brand, composition, or marketing
copy is reproduced. Licensing a library of real-brand profiles is a separate commercial step
that needs a permitted source; this seed exists so the ingestion, review, promotion, vector,
and recommendation pipeline runs end to end on realistic, discriminative data.
"""

from aromatwin.library.seed import DIRECTIONS, HOUSES, SeedProfile, build_seed_profiles

__all__ = ["DIRECTIONS", "HOUSES", "SeedProfile", "build_seed_profiles"]
