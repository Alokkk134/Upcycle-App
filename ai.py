"""Gemini-powered vision classification and idea generation.

The app works without an API key: every function here raises AIError on
failure, and app.py falls back to manual material selection.
"""

import io
import os

import streamlit as st
from PIL import Image, ImageOps
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
except ImportError:  # app still runs in manual mode
    genai = None
    types = None

DEFAULT_MODEL = "gemini-flash-latest"
FALLBACK_MODEL = "gemini-flash-lite-latest"
REQUEST_TIMEOUT_MS = 25_000
MAX_IMAGE_SIDE = 768


class AIError(Exception):
    """Raised when the AI step cannot produce a usable answer."""


class Classification(BaseModel):
    material_key: str = Field(description="One of the allowed material keys")
    item_name: str = Field(description="Short name of the object, e.g. '1 L water bottle'")
    material_type: str = Field(description="Material, e.g. 'PET plastic (#1)'")
    confidence: float = Field(description="Confidence from 0.0 to 1.0")
    is_hazardous: bool = Field(description="True for batteries, e-waste, chemicals, medicine, broken glass")
    reason: str = Field(description="One sentence explaining what visual cues led to this answer")
    prep_tip: str = Field(description="One short cleaning or safety tip before crafting with this item")


class GeneratedProject(BaseModel):
    title: str
    tagline: str
    use: str = Field(description="'School supply', 'Home decor', 'Home & garden' or 'Everyday use'")
    difficulty: str = Field(description="'Easy', 'Medium' or 'Hard'")
    time_minutes: int
    grams_diverted: int = Field(description="Estimated grams of waste reused by this project")
    tools: list[str]
    safety: str
    steps: list[str]


def _secret(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:  # no secrets.toml present
        value = None
    return value or os.environ.get(name)


def api_key() -> str | None:
    key = _secret("GEMINI_API_KEY")
    if key and "PASTE" not in key:
        return key
    return None


def is_available() -> bool:
    return genai is not None and api_key() is not None


@st.cache_resource(show_spinner=False)
def _client(key: str):
    # Fail fast instead of hanging: _generate handles fallback to the lighter model.
    return genai.Client(
        api_key=key,
        http_options=types.HttpOptions(
            timeout=REQUEST_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )


def _model() -> str:
    return _secret("GEMINI_MODEL") or DEFAULT_MODEL


def prepare_image(raw: bytes) -> bytes:
    """Fix rotation, shrink and re-encode as JPEG to keep requests small."""
    img = Image.open(io.BytesIO(raw))
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=85)
    return out.getvalue()


def _generate(contents, schema):
    if not is_available():
        raise AIError("AI is not configured (no Gemini API key).")
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=schema,
        temperature=0.4,
    )
    # Gemini returns 503 when a model is overloaded; try the lighter model before giving up.
    models = list(dict.fromkeys([_model(), FALLBACK_MODEL]))
    for i, model in enumerate(models):
        try:
            response = _client(api_key()).models.generate_content(
                model=model, contents=contents, config=config
            )
            break
        except Exception as exc:
            code = getattr(exc, "code", None)
            if code is None and "timeout" in type(exc).__name__.lower():
                code = 504
            if code in (500, 503, 504) and i < len(models) - 1:
                continue
            if code in (500, 503, 504):
                raise AIError("Gemini is overloaded right now. Please try again or pick your material manually.") from exc
            if code == 429:
                raise AIError("The free AI quota is busy right now. Please pick your material manually.") from exc
            if code in (401, 403):
                raise AIError("The Gemini API key was rejected. Check GEMINI_API_KEY.") from exc
            raise AIError(f"AI service error: {exc}") from exc

    parsed = response.parsed
    if parsed is None:
        raise AIError("AI returned an unreadable answer.")
    return parsed


@st.cache_data(show_spinner=False, ttl=3600, max_entries=200)
def classify_image(image_bytes: bytes, material_keys: tuple[str, ...]) -> dict:
    """Identify the waste item in a photo and map it to a known material key."""
    allowed = ", ".join(material_keys)
    prompt = (
        "You are the vision module of an upcycling app for school students. "
        "Look at the photo and identify the main household waste item.\n"
        f"Set material_key to exactly one of: {allowed}, not_upcyclable, unknown.\n"
        "- Use not_upcyclable for batteries, e-waste, chargers, bulbs, medicine or chemical "
        "containers, aerosol cans, broken glass, or heavily food-soiled packaging.\n"
        "- Use unknown if there is no clear waste item in the photo.\n"
        "- tetra_pak means milk/juice cartons; newspaper covers any loose paper; "
        "old_cloth covers clothes and fabric; cardboard_box covers any cardboard packaging.\n"
        "Be honest with confidence: below 0.6 if the photo is blurry or ambiguous."
    )
    contents = [types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"), prompt]
    result: Classification = _generate(contents, Classification)

    data = result.model_dump()
    if data["material_key"] not in (*material_keys, "not_upcyclable", "unknown"):
        data["material_key"] = "unknown"
    data["confidence"] = max(0.0, min(1.0, float(data["confidence"])))
    return data


@st.cache_data(show_spinner=False, ttl=3600, max_entries=200)
def generate_idea(material_name: str, item_name: str, existing_titles: tuple[str, ...]) -> dict:
    """Ask Gemini for one extra, student-safe upcycling project."""
    prompt = (
        "You help Grade 8–12 students upcycle household waste into useful school supplies "
        "or home decor.\n"
        f"Material: {material_name}. Item: {item_name or material_name}.\n"
        f"Suggest ONE new project that is different from: {', '.join(existing_titles)}.\n"
        "Rules: use only common household tools; no fire, candles, mains electricity, "
        "solvents or strong chemicals; mention adult supervision for any cutting, piercing "
        "or hot glue; 4 to 7 clear numbered-style steps; realistic time and grams_diverted."
    )
    result: GeneratedProject = _generate([prompt], GeneratedProject)
    return result.model_dump()
