"""ReCraft — Upcycled Material Craft & Design Recommender (Quest4Earth 2026)."""

import hashlib
import html
import json
from pathlib import Path

import streamlit as st

import ai

st.set_page_config(page_title="ReCraft · Upcycle Your Waste", page_icon="♻️", layout="centered")

GUIDES = json.loads((Path(__file__).parent / "data" / "guides.json").read_text(encoding="utf-8"))
MATERIALS = GUIDES["materials"]
NOT_UPCYCLABLE = GUIDES["not_upcyclable"]
MATERIAL_KEYS = tuple(MATERIALS)
LOW_CONFIDENCE = 0.6
DIFFICULTY_COLORS = {"Easy": "#2E7D32", "Medium": "#E08A00", "Hard": "#C62828"}
SAFETY_NOTE = "Adult supervision required when cutting plastic or metal, or using sharp tools."

st.markdown(
    """
    <style>
      .block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 820px; }
      .hero { background: linear-gradient(135deg, #1B5E20 0%, #43A047 100%); color: #fff;
              padding: 1.6rem 1.5rem; border-radius: 18px; margin-bottom: 1.2rem; }
      .hero h1 { color: #fff; font-size: 2rem; margin: 0 0 .3rem 0; padding: 0; }
      .hero p { margin: 0; font-size: 1.05rem; opacity: .95; }
      .tag { display: inline-block; padding: .18rem .6rem; border-radius: 999px; font-size: .78rem;
             font-weight: 600; margin: 0 .3rem .3rem 0; background: #E8F3E3; color: #1B5E20; }
      .tag.ai { background: #E3ECFB; color: #1A3E8C; }
      .tag.warn { background: #FFF1D6; color: #7A4B00; }
      .detect { border: 2px solid #43A047; border-radius: 16px; padding: 1rem 1.2rem; background: #fff; }
      .detect .big { font-size: 1.35rem; font-weight: 700; color: #1B2B1E; }
      .muted { color: #5B6B5E; font-size: .92rem; }
      .impact { background: #1B5E20; color: #fff; border-radius: 16px; padding: 1rem 1.2rem; }
      .impact b { font-size: 1.6rem; }
      div.stButton > button { border-radius: 10px; font-weight: 600; min-height: 2.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

state = st.session_state
state.setdefault("selected_project", None)
state.setdefault("built", [])
state.setdefault("ai_ideas", {})


def tag(text: str, kind: str = "") -> str:
    return f'<span class="tag {kind}">{html.escape(text)}</span>'


def difficulty_tag(level: str) -> str:
    color = DIFFICULTY_COLORS.get(level, "#555")
    return f'<span class="tag" style="background:{color};color:#fff">{html.escape(level)}</span>'


def material_label(key: str) -> str:
    m = MATERIALS[key]
    return f"{m['emoji']} {m['name']}"


# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
      <h1>♻️ ReCraft</h1>
      <p>Snap a photo of household waste. Get 3 upcycling ideas with step-by-step DIY guides.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

ai_ready = ai.is_available()
if not ai_ready:
    st.info(
        "**Demo mode:** AI vision is not configured on this deployment, "
        "so please choose your material manually below.",
        icon="ℹ️",
    )

# ---------- Step 1: Input ----------
st.subheader("1 · Show us your waste item")
modes = ["📷 Take a photo", "🖼️ Upload image", "📋 Choose material"] if ai_ready else ["📋 Choose material"]
mode = st.radio("Input method", modes, horizontal=True, label_visibility="collapsed")

image_file = None
if mode.startswith("📷"):
    image_file = st.camera_input("Point your camera at the item")
elif mode.startswith("🖼️"):
    image_file = st.file_uploader("Upload Waste Image", type=["jpg", "jpeg", "png", "webp"])

material_key = None
detection = None

if image_file is not None:
    raw = image_file.getvalue()
    image_id = hashlib.sha256(raw).hexdigest()[:16]
    if mode.startswith("🖼️"):
        st.image(raw, width=260)
    try:
        with st.spinner("🤖 AI is analysing your item..."):
            detection = ai.classify_image(ai.prepare_image(raw), MATERIAL_KEYS)
    except ai.AIError as err:
        st.warning(f"{err} You can still pick the material below.", icon="⚠️")
    except Exception:
        st.warning("We couldn't read that image. Try another photo or pick the material below.", icon="⚠️")

    if detection:
        # ---------- Step 2: Classification ----------
        st.subheader("2 · AI detection")
        key = detection["material_key"]
        pct = round(detection["confidence"] * 100)
        if key in MATERIALS:
            headline = f"{MATERIALS[key]['emoji']} {html.escape(detection['material_type'])} · {html.escape(detection['item_name'])}"
        elif key == "not_upcyclable":
            headline = f"⚠️ {html.escape(detection['item_name'])} — not safe to upcycle"
        else:
            headline = "❓ No clear waste item found"
        tags = tag("🤖 AI Vision · Google Gemini", "ai") + tag(f"Confidence: {pct}%")
        reason = html.escape(detection["reason"])
        st.markdown(
            f'<div class="detect">{tags}<div class="big">Detected: {headline}</div>'
            f'<div class="muted">{reason}</div></div>',
            unsafe_allow_html=True,
        )

        if key in MATERIALS:
            if detection["confidence"] < LOW_CONFIDENCE:
                st.warning("The AI isn't very sure about this one. Please confirm or correct it below.", icon="🧐")
            # Human in the loop: the user confirms or corrects the AI's answer.
            material_key = st.selectbox(
                "✅ Confirm or correct the material",
                MATERIAL_KEYS,
                index=MATERIAL_KEYS.index(key),
                format_func=material_label,
                key=f"confirm_{image_id}",
            )
        elif key == "not_upcyclable":
            material_key = "not_upcyclable"
        else:
            st.info("Try a clearer photo, or choose the material yourself:", icon="📷")

if material_key is None and (mode.startswith("📋") or image_file is not None):
    if detection is None or detection["material_key"] == "unknown":
        material_key = st.selectbox(
            "Select the material",
            MATERIAL_KEYS,
            index=None,
            placeholder="Choose a household waste item…",
            format_func=material_label,
        )

# ---------- Not-upcyclable path ----------
if material_key == "not_upcyclable":
    st.error(f"**{NOT_UPCYCLABLE['intro']}**", icon="⚠️")
    if detection and detection.get("prep_tip"):
        st.markdown(f"**AI tip:** {detection['prep_tip']}")
    st.markdown("#### How to dispose of it responsibly")
    for cat in NOT_UPCYCLABLE["categories"]:
        with st.expander(cat["title"]):
            st.write(cat["advice"])
    st.stop()

# ---------- Step 3: Recommendations ----------
if material_key:
    material = MATERIALS[material_key]
    st.subheader(f"3 · Upcycling ideas for your {material['name'].lower()}")
    st.caption(f"💡 {material['fact']}")
    prep = detection["prep_tip"] if detection and detection["material_key"] == material_key else material["prep"]
    st.markdown(f"**Before you start:** {prep}")

    projects = list(material["projects"])
    projects += state.ai_ideas.get(material_key, [])

    for start in range(0, len(projects), 3):
        cols = st.columns(3)
        for col, (i, proj) in zip(cols, enumerate(projects[start:start + 3], start=start)):
            with col, st.container(border=True):
                badge = tag("✨ AI-generated", "ai") if proj.get("ai_generated") else tag("✔ Verified guide")
                title = html.escape(proj["title"])
                tagline = html.escape(proj["tagline"])
                time_tag = tag("⏱ {} min".format(proj["time_minutes"]))
                st.markdown(
                    f"{badge}<br><b>Option {chr(65 + i)}: {title}</b>"
                    f"<div class='muted'>{tagline}</div>"
                    f"{difficulty_tag(proj['difficulty'])}{time_tag}",
                    unsafe_allow_html=True,
                )
                if st.button("View guide →", key=f"view_{material_key}_{i}", width="stretch"):
                    state.selected_project = (material_key, i)

    if ai_ready and not state.ai_ideas.get(material_key):
        if st.button("✨ Ask AI for a fresh idea", help="Gemini writes a new project for this material"):
            item_name = detection["item_name"] if detection else material["name"]
            try:
                with st.spinner("✨ AI is designing a new project..."):
                    idea = ai.generate_idea(
                        material["name"], item_name, tuple(p["title"] for p in material["projects"])
                    )
                idea["ai_generated"] = True
                state.ai_ideas[material_key] = [idea]
                st.rerun()
            except ai.AIError as err:
                st.warning(str(err), icon="⚠️")

    # ---------- Step 4: DIY guide ----------
    selected = state.selected_project
    if selected and selected[0] == material_key and selected[1] < len(projects):
        proj = projects[selected[1]]
        st.divider()
        st.subheader(f"4 · DIY guide: {proj['title']}")
        if proj.get("ai_generated"):
            st.markdown(
                tag("✨ AI-generated · not yet reviewed by our team", "warn")
                + "<div class='muted'>Check each step with a teacher or parent before you start.</div>",
                unsafe_allow_html=True,
            )

        c1, c2, c3 = st.columns(3)
        c1.metric("Difficulty", proj["difficulty"])
        c2.metric("Est. time", f"{proj['time_minutes']} min")
        c3.metric("Waste reused", f"{proj['grams_diverted']} g")

        st.markdown("##### 🧰 Required tools")
        st.markdown("\n".join(f"- {t}" for t in proj["tools"]))

        st.warning(f"**Safety:** {proj['safety']}  \n{SAFETY_NOTE}", icon="🦺")

        st.markdown("##### 📝 Step-by-step instructions")
        st.markdown("\n".join(f"{n}. {s}" for n, s in enumerate(proj["steps"], start=1)))

        # ---------- Step 5: Impact ----------
        st.markdown(
            f"""<div class="impact">🌍 By building this, you keep <b>{proj['grams_diverted']} g</b>
            of {material['category']} out of the local landfill!</div>""",
            unsafe_allow_html=True,
        )
        built_id = f"{material_key}:{proj['title']}"
        already = any(b["id"] == built_id for b in state.built)
        if st.button("✅ I built this!" if not already else "✅ Already counted", disabled=already, type="primary"):
            state.built.append(
                {"id": built_id, "title": proj["title"], "grams": proj["grams_diverted"], "category": material["category"]}
            )
            st.balloons()
            st.rerun()

# ---------- Impact tracker ----------
st.divider()
st.subheader("🌱 Your impact this session")
total_g = sum(b["grams"] for b in state.built)
c1, c2 = st.columns(2)
c1.metric("Projects built", len(state.built))
c2.metric("Waste kept out of landfill", f"{total_g / 1000:.2f} kg" if total_g >= 1000 else f"{total_g} g")
if state.built:
    st.caption(" · ".join(f"✅ {b['title']} ({b['grams']} g)" for b in state.built))
else:
    st.caption("Build a project and tap **I built this!** to start counting.")

with st.expander("ℹ️ How ReCraft works"):
    st.markdown(
        """
- **AI assists:** Google Gemini looks at your photo, identifies the item and material, and estimates its confidence. It can also suggest an extra project idea.
- **Humans lead:** you confirm or correct every detection, and all *Verified* guides were written and safety-checked by our team. AI-generated ideas are clearly labelled.
- **Impact numbers** are estimates based on typical item weights (e.g. a 500 ml PET bottle ≈ 25 g, a delivery box ≈ 200 g).
- **Privacy:** no login, nothing is stored. Photos are sent to Google's Gemini API for analysis only — please don't upload photos of people or personal documents.
        """
    )
st.caption("Built for Quest4Earth Hackathon 2026 · Sustainable Lifestyles")
