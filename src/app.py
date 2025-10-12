import os
import streamlit as st
from typing import List, Dict, Any
from recommender import CocktailRecommender

# -------------------- Page config -------------------- #
st.set_page_config(
    page_title="🍹 Cocktail Studio",
    page_icon="🍸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Styles -------------------- #
st.markdown(
    """
<style>
  :root{
    --bg: #0b0c10;
    --surface: #111317;
    --text: #f6f7fb;
    --muted: #b8c0d0;
    --accent: #FF6B6B;
    --accent-2: #7C4DFF;
    --chip: #2a2f3a;
    --pill-sim: #41c46a;
    --pill-tag: #ff9e44;
    --ring: rgba(255,255,255,.08);
    --card-grad-start: #22c55e;
    --card-grad-end: #065f46;
  }

  .block-container { padding-top: 2rem; }
  .main-header{
    font-size: clamp(2.2rem, 3.5vw, 3rem);
    font-weight: 800;
    letter-spacing: .5px;
    line-height: 1.1;
    margin: 0 0 .5rem 0;
    background: linear-gradient(90deg, var(--accent), #F8D66D);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .subtitle{
    margin-top: .1rem;
    color: var(--muted);
  }

  /* Utility bar */
  .bar{
    display:flex; gap: .75rem; align-items:center; flex-wrap: wrap;
    padding: .6rem .8rem; border-radius: 14px;
    background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
    border: 1px solid var(--ring);
  }

  /* Cards */
  .card{
    position: relative;
    background: linear-gradient(145deg, var(--card-grad-start), var(--card-grad-end));
    border: 1px solid var(--ring);
    border-radius: 18px;
    padding: 1rem 1.1rem 1.1rem 1.1rem;
    color: var(--text);
    box-shadow: 0 10px 28px rgba(0,0,0,.22);
    transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    min-height: 45px;
  }
  .card:hover{
    transform: translateY(-2px);
    border-color: rgba(255,255,255,.12);
    box-shadow: 0 14px 34px rgba(0,0,0,.28);
  }
  .card h3{
    margin: .15rem 0 .35rem 0;
    font-size: 1.12rem;
    line-height: 1.25;
    letter-spacing: .3px;
  }
  .row-meta{ display:flex; gap:.6rem; flex-wrap:wrap; margin:.15rem 0 .35rem 0; }
  .pill{
    display:inline-flex; align-items:center; gap:.35rem;
    padding: .22rem .55rem; border-radius: 999px;
    font-size: .82rem; font-weight: 600; letter-spacing:.2px;
    background: var(--chip); color: #fff;
    border: 1px solid var(--ring);
    opacity: .96;
  }
  .pill-sim{ background: var(--pill-sim); border:none; }
  .pill-tag{ background: var(--pill-tag); border:none; color:#1b1208; }
  .muted { color: var(--muted); }

  /* Tag grid */
  .tags{
    display: grid; grid-template-columns: repeat(2, minmax(0,1fr));
    gap: .35rem .35rem; margin-top: .2rem;
  }

  /* Empty state */
  .empty{
    padding: 1.25rem; border-radius: 16px;
    border: 1px dashed var(--ring);
    text-align:center; color: var(--muted);
  }

  /* Footer note inside card */
  .foot{
    position: absolute; bottom: .9rem; left: 1.1rem; right: 1.1rem;
    display:flex; justify-content: space-between; align-items:center; gap:.5rem;
    opacity:.95;
  }

  /* Sidebar polish */
  section[data-testid="stSidebar"] .stSelectbox, 
  section[data-testid="stSidebar"] .stSlider{
    margin-bottom: .6rem !important;
  }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_recommender():
    return CocktailRecommender()

@st.cache_data
def common_ingredients() -> List[str]:
    return [
        "vodka","gin","rum","whiskey","tequila","bourbon",
        "lime","lemon","orange","cranberry","pineapple",
        "mint","basil","simple syrup","triple sec","vermouth",
    ]

def _format_similarity(sim: Any) -> str:
    if sim is None: return "—"
    try:
        # assume model returns float in [0,1] or already percentage-like
        value = float(sim)
        if value <= 1.0: 
            value *= 100.0
        return f"{value:.0f}%"
    except Exception:
        return str(sim)

def _listize_ingredients(raw: Any, limit:int=14) -> List[str]:
    if not raw: 
        return []
    ings = [i.strip() for i in str(raw).split(",") if i.strip()]
    return ings[:limit]

def _ensure_state():
    st.session_state.setdefault("results", [])
    st.session_state.setdefault("last_mode", "")
    st.session_state.setdefault("favorites", set())
    st.session_state.setdefault("history", [])

def _push_history(label: str):
    if not label: 
        return
    if label not in st.session_state["history"]:
        st.session_state["history"] = ([label] + st.session_state["history"])[:8]

# -------------------- Card component -------------------- #
def display_cocktail(cocktail: Dict[str, Any]) -> None:
    name = cocktail.get("name","(unknown)")
    category = cocktail.get("category","—")
    alcoholic = cocktail.get("alcoholic","—")
    glass = cocktail.get("glass","—")
    sim_txt = _format_similarity(cocktail.get("similarity"))
    ings = _listize_ingredients(cocktail.get("ingredients"))
    recipe = cocktail.get("recipe","")

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"<h3>🍸 {name}</h3>", unsafe_allow_html=True)

    # Row: meta + similarity
    st.markdown(
        f"""
        <div class='row-meta'>
          <span class='pill'>Category: {category}</span>
          <span class='pill'>Type: {alcoholic}</span>
          <span class='pill'>Glass: {glass}</span>
          <span class='pill pill-sim'>Match {sim_txt}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Ingredients as chips (grid)
    if ings:
        st.markdown("<div class='muted' style='margin:.1rem 0 .2rem 0;'><b>Ingredients</b></div>", unsafe_allow_html=True)
        st.markdown("<div class='tags'>", unsafe_allow_html=True)
        for ing in ings:
            st.markdown(f"<span class='pill pill-tag'>{ing}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Recipe expander + sticky footer actions
    with st.expander("📖 Recipe"):
        if recipe:
            st.write(recipe)
        else:
            st.caption("No recipe text available for this item.")
        st.download_button(
            "⬇️ Save recipe",
            (recipe or f"{name}\n(No instructions available)"),
            file_name=f"{name.replace(' ', '_')}_recipe.txt",
            mime="text/plain",
            use_container_width=True,
        )

    # Footer actions (favorite toggle)
    is_fav = name in st.session_state["favorites"]
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button(("💖 Remove Favorite" if is_fav else "🤍 Add Favorite"),
                     key=f"fav-{name}", use_container_width=True):
            if is_fav:
                st.session_state["favorites"].discard(name)
                st.toast(f"Removed **{name}** from favorites", icon="🗑️")
            else:
                st.session_state["favorites"].add(name)
                st.toast(f"Saved **{name}** to favorites", icon="💖")
    with col2:
        st.caption(f"Similarity: {sim_txt}")

    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- Results grid -------------------- #
def render_cards(results: List[Dict[str, Any]], per_row: int = 3, compact: bool = False) -> None:
    if not results:
        st.markdown(
            "<div class='empty'>No cocktails found. Try different ingredients, lower the threshold, or switch modes.</div>",
            unsafe_allow_html=True,
        )
        return
    if compact:
        per_row = max(2, per_row + 1)  # slightly denser
    rows = [results[i:i+per_row] for i in range(0, len(results), per_row)]
    for row in rows:
        cols = st.columns(per_row)
        for c, item in zip(cols, row):
            with c:
                display_cocktail(item)

# =========================================================
# Main app
# =========================================================
def main():
    _ensure_state()

    # Header
    st.markdown('<h1 class="main-header">🍹 Cocktail Studio</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Discover, filter, and save your next favorite drink!</div>', unsafe_allow_html=True)
    st.write("")

    # Sidebar controls
    with st.sidebar:
        st.header("🎯 Preferences")
        mode = st.selectbox(
            "Explore mode",
            [
                "🔍 Search by Name",
                "🥃 By Ingredients",
                "🎭 By Style/Mood",
                "🎉 By Occasion",
                "🎲 Mixed Preferences",
                "📂 By Category",
                "🎰 Random Discovery",
            ],
        )

        st.divider()
        top_k = st.slider("Results (Top-K)", 3, 10, 5, help="How many cocktails to return")
        sim_thresh = st.slider(
            "Similarity threshold",
            0.0, 0.95, 0.60, 0.01,
            help="Minimum semantic match (vector). Affects vector-based searches.",
        )
        per_row = st.slider("Cards per row", 2, 4, 3)
        compact = st.toggle("Compact layout", value=False, help="Denser grid & spacing")

        st.divider()
        st.caption("Quick ingredients")
        quick = st.multiselect("Pick a few", common_ingredients())

        # Search history chips
        if st.session_state["history"]:
            st.caption("Recent searches")
            hist_cols = st.columns(min(4, len(st.session_state["history"])))
            for i, h in enumerate(st.session_state["history"]):
                with hist_cols[i % len(hist_cols)]:
                    if st.button(f"🕘 {h}", key=f"h-{i}"):
                        # re-run a name search quickly
                        _push_history(h)  # keep it at top
                        try:
                            rows = get_recommender().get_cocktail_by_name(h)
                            st.session_state["results"] = [get_recommender().format_result(r) for r in rows]
                            st.session_state["last_mode"] = "🔍 Search by Name"
                        except Exception as e:
                            st.error(f"History search failed: {e}")

        if st.button("Reset All", type="secondary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # Instantiate recommender once
    try:
        recommender = get_recommender()
    except Exception as e:
        st.error(f"Failed to initialize the recommender.\n\n{e}")
        st.stop()

    # Changing modes resets results
    if st.session_state["last_mode"] != mode:
        st.session_state["results"] = []
        st.session_state["last_mode"] = mode

    # 2-column layout: content + utilities
    left, right = st.columns([2.6, 1.0], vertical_alignment="top")

    with left:
        # ----------------- MODE: Search by Name -----------------
        if mode == "🔍 Search by Name":
            st.subheader("Search by Name")
            name = st.text_input("Type a cocktail name", placeholder="e.g., Margarita, Mojito, Negroni")
            if name:
                with st.spinner("Searching…"):
                    _push_history(name.strip())
                    rows = recommender.get_cocktail_by_name(name)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # ----------------- MODE: Ingredients (vector) -----------
        elif mode == "🥃 By Ingredients":
            st.subheader("Find by Ingredients")
            col_a, col_b = st.columns([2,3])
            with col_a:
                custom = st.text_input("Add custom ingredients", placeholder="comma-separated, e.g., gin, lemon")
            ingredients = quick.copy()
            if custom:
                ingredients += [x.strip() for x in custom.split(",") if x.strip()]
            if ingredients and st.button("Find Cocktails", type="primary"):
                with st.spinner("Finding perfect matches…"):
                    text = f"cocktail with {' and '.join(ingredients)}"
                    _push_history(", ".join(ingredients))
                    emb = recommender.get_user_preferences_embedding([text])
                    rows = recommender.search_similar_cocktails(emb, limit=top_k, threshold=sim_thresh)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # ----------------- MODE: Style (vector) -----------------
        elif mode == "🎭 By Style/Mood":
            st.subheader("Find by Style/Mood")
            style_opts = ["sweet","sour","bitter","strong","light","fruity","creamy","refreshing","exotic","classic","tropical"]
            styles = st.multiselect("Pick your vibe", style_opts, default=["refreshing"])
            if styles and st.button("Find Cocktails", type="primary"):
                with st.spinner("Finding your mood…"):
                    text = f"cocktail that is {' and '.join(styles)}"
                    _push_history("style: " + ", ".join(styles))
                    emb = recommender.get_user_preferences_embedding([text])
                    rows = recommender.search_similar_cocktails(emb, limit=top_k, threshold=sim_thresh)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # ----------------- MODE: Occasion (vector) --------------
        elif mode == "🎉 By Occasion":
            st.subheader("Find by Occasion")
            occasion = st.selectbox(
                "Occasion",
                ["", "party", "date night", "summer evening", "winter warmer", "brunch", "after dinner", "celebration", "relaxing at home"],
                index=1
            )
            if occasion and st.button("Find Cocktails", type="primary"):
                with st.spinner("Mixing for the moment…"):
                    text = f"cocktail for {occasion}"
                    _push_history(f"occasion: {occasion}")
                    emb = recommender.get_user_preferences_embedding([text])
                    rows = recommender.search_similar_cocktails(emb, limit=top_k, threshold=sim_thresh)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # ----------------- MODE: Mixed (vector) -----------------
        elif mode == "🎲 Mixed Preferences":
            st.subheader("Mix & Match")
            c1, c2 = st.columns(2)
            with c1:
                ing = st.multiselect("Ingredients", common_ingredients())
                sty = st.multiselect("Style", ["sweet","sour","strong","light","fruity","refreshing"])
            with c2:
                occ = st.selectbox("Occasion", ["", "party","date night","summer","winter","brunch"])
                alc = st.selectbox("Alcoholic preference", ["", "Alcoholic","Non alcoholic","Optional alcohol"])
            if any([ing, sty, occ, alc]) and st.button("Find My Perfect Cocktail", type="primary"):
                with st.spinner("Analyzing preferences…"):
                    parts: List[str] = []
                    if ing: parts.append(f"contains {' and '.join(ing)}")
                    if sty: parts.append(f"is {' and '.join(sty)}")
                    if occ: parts.append(f"perfect for {occ}")
                    if alc: parts.append(f"is {alc}")
                    _push_history("mix: " + "; ".join(parts))
                    emb = recommender.get_user_preferences_embedding(parts)
                    rows = recommender.search_similar_cocktails(emb, limit=top_k, threshold=sim_thresh)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # ----------------- MODE: Category (non-vector) ----------
        elif mode == "📂 By Category":
            st.subheader("Browse by Category")
            cat = st.selectbox(
                "Choose a category",
                ["", "Ordinary Drink", "Cocktail", "Shot", "Coffee / Tea", "Homemade Liqueur", "Punch / Party Drink", "Beer", "Soft Drink"]
            )
            if cat:
                with st.spinner("Loading category…"):
                    _push_history(f"category: {cat}")
                    rows = recommender.get_cocktail_by_category(cat, limit=top_k)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # ----------------- MODE: Random (non-vector) ------------
        elif mode == "🎰 Random Discovery":
            st.subheader("Surprise Me")
            st.caption("Let AI inspire you with random cocktails.")
            if st.button("🎲 Roll", type="primary"):
                with st.spinner("Shuffling…"):
                    _push_history("random")
                    rows = recommender.get_random_cocktails(limit=top_k)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # ----------------- Results ------------------------------
        if st.session_state["results"]:
            st.divider()
            st.subheader(f"🍸 Results ({len(st.session_state['results'])})")
            render_cards(st.session_state["results"], per_row=per_row, compact=compact)

    with right:
        st.subheader("📊 Controls")
        st.caption("These affect similarity-based searches.")
        st.metric("Top-K", top_k)
        st.metric("Similarity ≥", f"{int(sim_thresh * 100)}%")
        st.caption("Raise for stricter matches; lower for more variety.")

        st.subheader("🧰 Utilities")
        if st.session_state["results"]:
            # lightweight CSV export of names + similarity
            import pandas as pd
            simple = [
                {
                    "name": r.get("name",""),
                    "similarity": r.get("similarity",""),
                    "category": r.get("category",""),
                    "alcoholic": r.get("alcoholic",""),
                } for r in st.session_state["results"]
            ]
            df = pd.DataFrame(simple)
            st.download_button(
                "⬇️ Export results (.csv)",
                df.to_csv(index=False).encode(),
                file_name="cocktails_results.csv",
                use_container_width=True,
            )
        st.toggle("Show favorites only (below)", key="show_favs", value=False)

        st.subheader("💡 Tips")
        st.info(
            "- Be specific with ingredients\n"
            "- Combine multiple styles (e.g., *sweet* + *refreshing*)\n"
            "- Try different occasions\n"
            "- Random discovery = new ideas\n"
            "- Partial names work too!"
        )

        st.subheader("🛠️ Status")
        db_host = os.getenv("DB_HOST", os.getenv("POSTGRES_HOST", "127.0.0.1"))
        db_port = os.getenv("DB_PORT", os.getenv("POSTGRES_PORT", "5432"))
        model = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
        st.write(f"**DB**: {db_host}:{db_port}")
        st.write("**Model**:", model)

        # Favorites
        if st.session_state["favorites"]:
            st.subheader(f"💖 Favorites ({len(st.session_state['favorites'])})")
            for fav in sorted(st.session_state["favorites"]):
                st.write("•", fav)

    if st.session_state.get("show_favs") and st.session_state["favorites"] and st.session_state["results"]:
        fav_filter = {n for n in st.session_state["favorites"]}
        favs = [r for r in st.session_state["results"] if r.get("name") in fav_filter]
        st.divider()
        st.subheader(f"💖 Favorites in this result set ({len(favs)})")
        render_cards(favs, per_row=per_row, compact=True)

if __name__ == "__main__":
    main()
