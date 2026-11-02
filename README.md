# ♻️ ReCraft — Upcycled Material Craft & Design Recommender

**Quest4Earth Hackathon 2026 · Focus Area: Sustainable Lifestyles**

Snap a photo of a household waste item (plastic bottle, cardboard box, tin can, old t-shirt…) and get
3 practical upcycling projects with step-by-step DIY guides, safety notes and an estimate of the waste you kept
out of landfill.

> **Human intelligence leads, AI assists.** Google Gemini identifies the item; students confirm or correct it;
> every *Verified* guide was written and safety-checked by our team. AI-generated ideas are clearly labelled.

## How it works

1. **Input** — take a photo, upload an image, or pick the material from a list.
2. **AI vision** — Gemini classifies the item and returns material, confidence and a short reason.
3. **Human check** — the user confirms or corrects the detected material (low-confidence results are flagged).
4. **Recommendations** — 3 verified projects per material, plus an optional "✨ Ask AI for a fresh idea".
5. **DIY guide** — difficulty, time, tools, safety disclaimer and numbered steps.
6. **Impact** — grams of waste reused, tracked for the session.

Hazardous items (batteries, e-waste, chemicals, broken glass) are detected and routed to safe-disposal advice
instead of craft ideas.

**Materials covered:** plastic bottle · cardboard box · tin can · old cloth · glass jar · newspaper · Tetra Pak
(21 verified guides in [`data/guides.json`](data/guides.json)).

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Put your free Gemini API key (from <https://aistudio.google.com/apikey>) in `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-key"
```

```bash
streamlit run app.py
```

Without a key the app runs in **demo mode** (manual material selection only).

## Deploy (Streamlit Community Cloud — free)

1. Go to <https://share.streamlit.io> → **Create app** → pick this repo, branch `main`, file `app.py`.
2. **Advanced settings → Secrets**: `GEMINI_API_KEY = "your-key"`.
3. Deploy and share the `*.streamlit.app` link.

Optional secret: `GEMINI_MODEL` (default `gemini-flash-latest`).

## Tech

Python · Streamlit · Google Gemini API (`google-genai`) · Pillow. No database, no login.

## Privacy

Nothing is stored. Photos are resized and sent to the Gemini API for classification only.
Please don't upload photos of people or personal documents.
