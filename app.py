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
DIFFICULTY_COLORS = {"Easy": "#2E7D32", "Medium": "#B86E00", "Hard": "#C62828"}
USE_ICONS = {"School supply": "✏️", "Home decor": "🖼️", "Home & garden": "🪴", "Everyday use": "👜"}
SAFETY_NOTE = "Adult supervision required when cutting plastic or metal, or using sharp tools."
STEPS = ["Item", "Detect", "Ideas", "Guide", "Impact"]
# (min grams, badge, name): levels shown in the impact tracker.
ECO_LEVELS = [(0, "🌱", "Seedling"), (100, "🌿", "Sprout"), (500, "🌳", "Tree"), (1000, "🌍", "Earth Hero")]
BOTTLE_G = 25  # a 500 ml PET bottle, used for the "bottles saved" comparison

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');
      html, body, [class*="st-"], .stMarkdown, button, input { font-family: 'Nunito', sans-serif; }
      .block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 860px; }
      h2, h3 { letter-spacing: -.01em; }

      .hero { position: relative; overflow: hidden; color: #fff; border-radius: 22px;
              padding: 1.7rem 1.6rem 1.4rem; margin-bottom: 1rem;
              background: radial-gradient(circle at 85% 15%, rgba(255,255,255,.18) 0 18%, transparent 19%),
                          linear-gradient(135deg, #154B19 0%, #2E7D32 55%, #66BB6A 100%); }
      .hero h1 { color: #fff; font-size: 2.2rem; font-weight: 800; margin: 0 0 .25rem; padding: 0; }
      .hero p { margin: 0 0 .9rem; font-size: 1.08rem; opacity: .95; max-width: 34rem; }
      .hero .chip { display: inline-block; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.3);
                    padding: .22rem .7rem; border-radius: 999px; font-size: .8rem; font-weight: 700;
                    margin: 0 .35rem .35rem 0; }

      .stepper { display: flex; gap: .4rem; margin: 0 0 1.2rem; }
      .stepper .s { flex: 1; text-align: center; font-size: .78rem; font-weight: 700; color: #7A8A7D; }
      .stepper .bar { height: 6px; border-radius: 99px; background: #DDE8D8; margin-bottom: .3rem; }
      .stepper .s.done .bar { background: #66BB6A; }
      .stepper .s.now .bar { background: #2E7D32; }
      .stepper .s.now, .stepper .s.done { color: #1B5E20; }

      .section { display: flex; align-items: center; gap: .6rem; margin: 1.4rem 0 .6rem; }
      .section .num { width: 2rem; height: 2rem; border-radius: 50%; background: #2E7D32; color: #fff;
                      display: grid; place-items: center; font-weight: 800; flex-shrink: 0; }
      .section .ttl { font-size: 1.3rem; font-weight: 800; color: #1B2B1E; line-height: 1.2; }

      .tag { display: inline-block; padding: .18rem .6rem; border-radius: 999px; font-size: .76rem;
             font-weight: 700; margin: 0 .3rem .3rem 0; background: #E8F3E3; color: #1B5E20; }
      .tag.ai { background: #E3ECFB; color: #1A3E8C; }
      .tag.warn { background: #FFF1D6; color: #7A4B00; }
      .tag.ghost { background: #F1F4EF; color: #44524A; }

      .card { background: #fff; border: 1px solid #DDE8D8; border-radius: 18px; padding: 1.1rem 1.2rem;
              box-shadow: 0 2px 10px rgba(27,94,32,.06); }
      .detect .big { font-size: 1.3rem; font-weight: 800; color: #1B2B1E; margin: .2rem 0; }
      .meter { height: 10px; border-radius: 99px; background: #EEF2EC; overflow: hidden; margin: .5rem 0 .3rem; }
      .meter > div { height: 100%; border-radius: 99px; }
      .muted { color: #5B6B5E; font-size: .92rem; }

      .proj .use { font-size: 1.9rem; line-height: 1; margin-bottom: .4rem; }
      .proj .opt { font-size: .72rem; font-weight: 800; color: #7A8A7D; text-transform: uppercase; letter-spacing: .06em; }
      .proj .ttl { font-weight: 800; font-size: 1.05rem; color: #1B2B1E; margin: .1rem 0 .3rem; }
      .proj .muted { min-height: 2.8rem; margin-bottom: .5rem; }

      .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: .6rem; margin: .8rem 0; }
      .stat { background: #F1F7EE; border-radius: 14px; padding: .7rem .5rem; text-align: center; }
      .stat .v { font-size: 1.15rem; font-weight: 800; color: #1B2B1E; }
      .stat .l { font-size: .74rem; font-weight: 700; color: #5B6B5E; text-transform: uppercase; letter-spacing: .04em; }
      @media (max-width: 640px) { .stats { grid-template-columns: repeat(2, 1fr); } .hero h1 { font-size: 1.8rem; } }

      .impact { background: linear-gradient(135deg, #154B19, #2E7D32); color: #fff; border-radius: 18px;
                padding: 1.1rem 1.3rem; margin: 1rem 0 .7rem; font-size: 1.02rem; }
      .impact b { font-size: 1.5rem; }
      .eco { display: flex; align-items: center; gap: 1rem; }
      .eco .badge { font-size: 2.8rem; line-height: 1; }
      .eco .lvl { font-size: 1.2rem; font-weight: 800; color: #1B2B1E; }
      .eco .big { font-size: 2rem; font-weight: 800; color: #1B5E20; line-height: 1.1; }

      div.stButton > button { border-radius: 12px; font-weight: 700; min-height: 2.7rem; }
      [data-testid="stPills"] button { font-weight: 700; }
      [data-testid="stVerticalBlockBorderWrapper"] { border-radius: 18px; }
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


def section(num: int, title: str) -> None:
    st.markdown(
        f'<div class="section"><div class="num">{num}</div><div class="ttl">{html.escape(title)}</div></div>',
        unsafe_allow_html=True,
    )


def fmt_grams(g: int) -> str:
    return f"{g / 1000:.2f} kg" if g >= 1000 else f"{g} g"


def eco_level(grams: int):
    """Return (badge, name, next level or None) for a running total."""
    current = ECO_LEVELS[0]
    nxt = None
    for level in ECO_LEVELS:
        if grams >= level[0]:
            current = level
        elif nxt is None:
            nxt = level
    return current, nxt


# ---------- Header ----------
ai_ready = ai.is_available()
guide_count = sum(len(m["projects"]) for m in MATERIALS.values())
ai_chip = "🤖 AI vision on" if ai_ready else "📋 Demo mode"
st.markdown(
    f"""
    <div class="hero">
      <h1>♻️ ReCraft</h1>
      <p>Turn household waste into school supplies and home decor. Snap a photo and get 3 DIY ideas with step-by-step guides.</p>
      <span class="chip">{ai_chip}</span><span class="chip">🧩 {len(MATERIALS)} materials</span>
      <span class="chip">✔ {guide_count} verified guides</span><span class="chip">🔓 No login</span>
    </div>
    """,
    unsafe_allow_html=True,
)
stepper = st.empty()  # filled in at the end, once we know how far the user got
progress = 0

if not ai_ready:
    st.info(
        "**Demo mode:** AI vision is not configured on this deployment, "
        "so please choose your material from the list below.",
        icon="ℹ️",
    )

# ---------- Step 1: Input ----------
section(1, "Show us your waste item")
modes = ["📷 Camera", "🖼️ Upload", "📋 Pick material"] if ai_ready else ["📋 Pick material"]
mode = st.segmented_control(
    "Input method", modes, default=modes[1] if ai_ready else modes[0], label_visibility="collapsed"
) or modes[-1]

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
    try:
        with st.spinner("🤖 AI is looking at your item..."):
            detection = ai.classify_image(ai.prepare_image(raw), MATERIAL_KEYS)
    except ai.AIError as err:
        st.warning(f"{err} You can still pick the material below.", icon="⚠️")
    except Exception:
        st.warning("We couldn't read that image. Try another photo or pick the material below.", icon="⚠️")

    if detection:
        # ---------- Step 2: Classification ----------
        progress = 1
        section(2, "AI detection")
        key = detection["material_key"]
        conf = detection["confidence"]
        pct = round(conf * 100)
        if key in MATERIALS:
            headline = f"{MATERIALS[key]['emoji']} {html.escape(detection['item_name'])}"
            sub = html.escape(detection["material_type"])
        elif key == "not_upcyclable":
            headline = f"⚠️ {html.escape(detection['item_name'])}"
            sub = "Not safe to upcycle"
        else:
            headline = "❓ No clear waste item found"
            sub = "Try a closer, well-lit photo"
        meter_color = "#2E7D32" if conf >= 0.8 else "#E08A00" if conf >= LOW_CONFIDENCE else "#C62828"

        target = st
        if mode.startswith("🖼️"):  # the camera widget already shows its own preview
            img_col, target = st.columns([1, 2], vertical_alignment="center")
            img_col.image(raw, width=200)
        target.markdown(
            f'<div class="card detect">{tag("🤖 AI Vision · Google Gemini", "ai")}'
            f'<div class="big">{headline}</div><div class="muted">{sub}</div>'
            f'<div class="meter"><div style="width:{pct}%;background:{meter_color}"></div></div>'
            f'<div class="muted"><b>{pct}% confident</b> · {html.escape(detection["reason"])}</div></div>',
            unsafe_allow_html=True,
        )

        if key in MATERIALS:
            if conf < LOW_CONFIDENCE:
                st.warning("The AI isn't very sure about this one. Please confirm or correct it below.", icon="🧐")
            # Human in the loop: the user confirms or corrects the AI's answer.
            material_key = st.pills(
                "✅ Is this right? Tap to correct the material if needed",
                MATERIAL_KEYS,
                default=key,
                format_func=material_label,
                key=f"confirm_{image_id}",
            ) or key
        elif key == "not_upcyclable":
            material_key = "not_upcyclable"
        else:
            st.info("Try a clearer photo, or pick the material yourself:", icon="📷")

if material_key is None and (mode.startswith("📋") or image_file is not None):
    if detection is None or detection["material_key"] == "unknown":
        material_key = st.pills(
            "Tap the item you want to upcycle",
            MATERIAL_KEYS,
            format_func=material_label,
            key="manual_material",
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
    stepper.markdown(
        '<div class="stepper">' + "".join(
            f'<div class="s {"done" if i <= 1 else ""}"><div class="bar"></div>{s}</div>' for i, s in enumerate(STEPS)
        ) + "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

# ---------- Step 3: Recommendations ----------
if material_key:
    progress = 2
    material = MATERIALS[material_key]
    section(3, f"Upcycling ideas for your {material['name'].lower()}")
    prep = detection["prep_tip"] if detection and detection["material_key"] == material_key else material["prep"]
    st.markdown(
        f'<div class="card" style="padding:.8rem 1.1rem">💡 <b>Did you know?</b> {html.escape(material["fact"])}'
        f'<div class="muted" style="margin-top:.35rem">🧼 <b>Before you start:</b> {html.escape(prep)}</div></div>',
        unsafe_allow_html=True,
    )
    st.write("")

    projects = list(material["projects"])
    projects += state.ai_ideas.get(material_key, [])
    selected = state.selected_project

    for start in range(0, len(projects), 3):
        cols = st.columns(3)
        for col, (i, proj) in zip(cols, enumerate(projects[start:start + 3], start=start)):
            is_selected = selected == (material_key, i)
            with col, st.container(border=True):
                badge = tag("✨ AI idea", "ai") if proj.get("ai_generated") else tag("✔ Verified")
                st.markdown(
                    f'<div class="proj"><div class="use">{USE_ICONS.get(proj.get("use"), "♻️")}</div>'
                    f'<div class="opt">Option {chr(65 + i)} · {html.escape(proj.get("use", "Upcycle"))}</div>'
                    f'<div class="ttl">{html.escape(proj["title"])}</div>'
                    f'<div class="muted">{html.escape(proj["tagline"])}</div>'
                    f'{difficulty_tag(proj["difficulty"])}{tag("⏱ {} min".format(proj["time_minutes"]), "ghost")}'
                    f'{tag("♻ {} g".format(proj["grams_diverted"]), "ghost")}{badge}</div>',
                    unsafe_allow_html=True,
                )
                label = "Viewing guide ↓" if is_selected else "View guide →"
                if st.button(label, key=f"view_{material_key}_{i}", width="stretch",
                             type="primary" if is_selected else "secondary"):
                    state.selected_project = (material_key, i)
                    st.rerun()

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
    if selected and selected[0] == material_key and selected[1] < len(projects):
        progress = 3
        idx = selected[1]
        proj = projects[idx]
        section(4, f"DIY guide: {proj['title']}")
        st.markdown(f'<div class="muted">{html.escape(proj["tagline"])}</div>', unsafe_allow_html=True)
        if proj.get("ai_generated"):
            st.markdown(
                tag("✨ AI-generated · not yet reviewed by our team", "warn")
                + "<div class='muted'>Check each step with a teacher or parent before you start.</div>",
                unsafe_allow_html=True,
            )

        diff_color = DIFFICULTY_COLORS.get(proj["difficulty"], "#1B2B1E")
        st.markdown(
            f'<div class="stats">'
            f'<div class="stat"><div class="v" style="color:{diff_color}">{html.escape(proj["difficulty"])}</div><div class="l">Difficulty</div></div>'
            f'<div class="stat"><div class="v">{proj["time_minutes"]} min</div><div class="l">Est. time</div></div>'
            f'<div class="stat"><div class="v">{proj["grams_diverted"]} g</div><div class="l">Waste reused</div></div>'
            f'<div class="stat"><div class="v">{html.escape(str(proj.get("grade", "All")))}</div><div class="l">Grade</div></div>'
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("##### 🧰 What you'll need")
        st.markdown("".join(tag(t, "ghost") for t in proj["tools"]), unsafe_allow_html=True)

        safety = proj["safety"] if "supervision" in proj["safety"].lower() else f"{proj['safety']}  \n{SAFETY_NOTE}"
        st.warning(f"**Safety:** {safety}", icon="🦺")

        st.markdown("##### 📝 Step-by-step instructions")
        step_keys = [f"step_{material_key}_{idx}_{n}" for n in range(len(proj["steps"]))]
        done = sum(bool(state.get(k)) for k in step_keys)
        st.progress(done / len(step_keys), text=f"{done} of {len(step_keys)} steps done")
        for n, (step, k) in enumerate(zip(proj["steps"], step_keys), start=1):
            st.checkbox(f"**Step {n}.** {step}", key=k)

        # ---------- Step 5: Impact ----------
        st.markdown(
            f"""<div class="impact">🌍 By building this, you keep <b>{proj['grams_diverted']} g</b>
            of {material['category']} out of the local landfill!</div>""",
            unsafe_allow_html=True,
        )
        built_id = f"{material_key}:{proj['title']}"
        already = any(b["id"] == built_id for b in state.built)
        if already:
            progress = 4
        label = "✅ Already counted" if already else (
            "🎉 I built this!" if done == len(step_keys) else "✅ I built this!"
        )
        if st.button(label, disabled=already, type="primary", width="stretch"):
            state.built.append(
                {"id": built_id, "title": proj["title"], "grams": proj["grams_diverted"], "category": material["category"]}
            )
            st.balloons()
            st.rerun()

stepper.markdown(
    '<div class="stepper">' + "".join(
        f'<div class="s {"done" if i < progress else "now" if i == progress else ""}"><div class="bar"></div>{s}</div>'
        for i, s in enumerate(STEPS)
    ) + "</div>",
    unsafe_allow_html=True,
)

# ---------- Impact tracker ----------
st.divider()
st.markdown("### 🌱 Your impact this session")
total_g = sum(b["grams"] for b in state.built)
(min_g, badge, level_name), nxt = eco_level(total_g)
with st.container(border=True):
    left, right = st.columns([3, 2], vertical_alignment="center")
    left.markdown(
        f'<div class="eco"><div class="badge">{badge}</div><div>'
        f'<div class="lvl">{level_name}</div>'
        f'<div class="muted">{len(state.built)} project{"s" if len(state.built) != 1 else ""} built</div></div></div>',
        unsafe_allow_html=True,
    )
    right.markdown(
        f'<div style="text-align:right"><div class="big" style="font-size:2rem;font-weight:800;color:#1B5E20">'
        f'{fmt_grams(total_g)}</div><div class="muted">kept out of landfill</div></div>',
        unsafe_allow_html=True,
    )
    if nxt:
        span = nxt[0] - min_g
        st.progress((total_g - min_g) / span, text=f"{nxt[0] - total_g} g more to reach {nxt[1]} {nxt[2]}")
    else:
        st.progress(1.0, text="Top level reached. You're an Earth Hero!")
    if state.built:
        bottles = total_g / BOTTLE_G
        st.caption(
            f"That's about the weight of **{bottles:.0f} plastic bottles**. "
            + " · ".join(f"✅ {html.escape(b['title'])}" for b in state.built)
        )
    else:
        st.caption("Build a project and tap **I built this!** to start counting.")

with st.expander("ℹ️ How ReCraft works"):
    st.markdown(
        """
- **AI assists:** Google Gemini looks at your photo, identifies the item and material, and estimates its confidence. It can also suggest an extra project idea.
- **Humans lead:** you confirm or correct every detection, and all *Verified* guides were written and safety-checked by our team. AI-generated ideas are clearly labelled.
- **Impact numbers** are estimates based on typical item weights (e.g. a 500 ml PET bottle ≈ 25 g, a delivery box ≈ 200 g).
- **Privacy:** no login, nothing is stored. Photos are sent to Google's Gemini API for analysis only. Please don't upload photos of people or personal documents.
        """
    )
st.caption("Built for Quest4Earth Hackathon 2026 · Sustainable Lifestyles")
