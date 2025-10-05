import os
import streamlit as st
from typing import List, Dict, Any
from recommender import CocktailRecommender  

# -------------------- Page config -------------------- #
st.set_page_config(
    page_title="🍹 Cocktail Suggestions",
    page_icon="🍹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- Styles -------------------- #
st.markdown(
    """
<style>
    :root {
        --card-grad-start: #667eea;
        --card-grad-end: #764ba2;
        --tag-bg: #FF9800;
        --sim-bg: #4CAF50;
    }
    [data-theme="dark"] :root {
        --card-grad-start: #3949ab;
        --card-grad-end: #6a1b9a;
        --tag-bg: #ffb74d;
        --sim-bg: #43a047;
    }
    .main-header {
        font-size: 3rem;
        color: #FF6B6B;
        text-align: center;
        margin: 0 0 1.25rem 0;
    }
    .card {
        background: linear-gradient(135deg, var(--card-grad-start) 0%, var(--card-grad-end) 100%);
        padding: 1rem 1.2rem;
        border-radius: 16px;
        color: #fff;
        box-shadow: 0 6px 24px rgba(0,0,0,.12);
    }
    .card h3 { margin: .1rem 0 .6rem 0; }
    .pill {
        display: inline-block;
        padding: .25rem .6rem;
        border-radius: 999px;
        font-size: .85rem;
        margin: .15rem .25rem .15rem 0;
    }
    .pill-sim { background: var(--sim-bg); color: #fff; }
    .pill-tag { background: var(--tag-bg); color: #fff; }
    .muted { opacity: .9; }
    hr { border: none; height: 1px; background: #e6e6e6; margin: 1rem 0; }
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
        "vodka", "gin", "rum", "whiskey", "tequila", "bourbon",
        "lime", "lemon", "orange", "cranberry", "pineapple",
        "mint", "basil", "simple syrup", "triple sec", "vermouth",
    ]


def display_cocktail(cocktail: Dict[str, Any]) -> None:
    """Card UI for a single cocktail."""
    with st.container(border=True):
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"<h3>🍹 {cocktail['name']}</h3>", unsafe_allow_html=True)

        meta_cols = st.columns(3)
        with meta_cols[0]:
            sim = cocktail.get("similarity")
            sim_txt = f"{sim}%" if sim is not None else "—"
            st.markdown(f"<span class='pill pill-sim'>Match: {sim_txt}</span>", unsafe_allow_html=True)
        st.markdown(
            f"<span class='muted'><b>Category:</b> {cocktail.get('category','—')}</span>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<span class='muted'><b>Type:</b> {cocktail.get('alcoholic','—')}</span>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"<div class='muted'><b>Glass:</b> {cocktail.get('glass','—')}</div>",
            unsafe_allow_html=True,
        )

        if cocktail.get("ingredients"):
            ings = [i.strip() for i in str(cocktail["ingredients"]).split(",") if i.strip()]
            st.markdown("<div class='muted' style='margin:.5rem 0 .25rem 0;'><b>Ingredients:</b></div>", unsafe_allow_html=True)
            tag_cols = st.columns(4)
            for i, ing in enumerate(ings[:12]):
                with tag_cols[i % 4]:
                    st.markdown(f"<span class='pill pill-tag'>{ing}</span>", unsafe_allow_html=True)

        if cocktail.get("recipe"):
            with st.expander("📖 View Recipe"):
                st.write(cocktail["recipe"])
                st.download_button(
                    "⬇️ Download recipe",
                    cocktail["recipe"],
                    file_name=f"{cocktail['name'].replace(' ', '_')}_recipe.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

        st.markdown("</div>", unsafe_allow_html=True)


def render_cards(results: List[Dict[str, Any]], per_row: int = 2) -> None:
    if not results:
        st.info("No cocktails found. Try adjusting your filters.")
        return
    rows = [results[i : i + per_row] for i in range(0, len(results), per_row)]
    for row in rows:
        cols = st.columns(per_row)
        for c, item in zip(cols, row):
            with c:
                display_cocktail(item)


def main():
    st.markdown('<h1 class="main-header">🍹 Cocktail Suggestions</h1>', unsafe_allow_html=True)
    st.caption("### Discover your next favorite drink with AI and vector similarity!")

    st.session_state.setdefault("results", [])
    st.session_state.setdefault("last_mode", "")

    with st.sidebar:
        st.header("🎯 Preferences")
        mode = st.selectbox(
            "How do you want to explore?",
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
        top_k = st.slider("Results (Top-K)", 3, 24, 10, help="How many cocktails to return")
        sim_thresh = st.slider(
            "Similarity threshold",
            0.0,
            0.9,
            0.30,
            0.01,
            help="Minimum semantic match (vector). Only affects similarity-based searches.",
        )

        st.divider()
        st.caption("Quick ingredients")
        quick = st.multiselect("Pick a few to start", common_ingredients())

        if st.button("Reset Filters", use_container_width=True):
            st.session_state["results"] = []
            st.session_state["last_mode"] = ""
            st.rerun()

    try:
        recommender = get_recommender()
    except Exception as e:
        st.error(f"Failed to initialize the recommender.\n\n{e}")
        st.stop()

    if st.session_state["last_mode"] != mode:
        st.session_state["results"] = []
        st.session_state["last_mode"] = mode

    left, right = st.columns([2.4, 1.0], vertical_alignment="top")

    with left:
        # --- Search by Name (not vector-based) ---
        if mode == "🔍 Search by Name":
            st.subheader("Search by Name")
            name = st.text_input("Type a cocktail name", placeholder="e.g., Margarita, Mojito, Negroni")
            if name:
                with st.spinner("Searching…"):
                    rows = recommender.get_cocktail_by_name(name)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # --- By Ingredients (vector-based) ---
        elif mode == "🥃 By Ingredients":
            st.subheader("Find by Ingredients")
            custom = st.text_input("Add custom ingredients (comma-separated)")
            ingredients = quick.copy()
            if custom:
                ingredients += [x.strip() for x in custom.split(",") if x.strip()]
            if ingredients and st.button("Find Cocktails", type="primary"):
                with st.spinner("Finding perfect matches…"):
                    # Build embedding here to pass threshold
                    text = f"cocktail with {' and '.join(ingredients)}"
                    emb = recommender.get_user_preferences_embedding([text])
                    rows = recommender.search_similar_cocktails(emb, limit=top_k, threshold=sim_thresh)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # --- By Style/Mood (vector-based) ---
        elif mode == "🎭 By Style/Mood":
            st.subheader("Find by Style/Mood")
            style_opts = ["sweet", "sour", "bitter", "strong", "light", "fruity", "creamy", "refreshing", "exotic", "classic", "tropical"]
            styles = st.multiselect("Pick your vibe", style_opts)
            if styles and st.button("Find Cocktails", type="primary"):
                with st.spinner("Finding your mood…"):
                    text = f"cocktail that is {' and '.join(styles)}"
                    emb = recommender.get_user_preferences_embedding([text])
                    rows = recommender.search_similar_cocktails(emb, limit=top_k, threshold=sim_thresh)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # --- By Occasion (vector-based) ---
        elif mode == "🎉 By Occasion":
            st.subheader("Find by Occasion")
            occasion = st.selectbox(
                "Occasion",
                ["", "party", "date night", "summer evening", "winter warmer", "brunch", "after dinner", "celebration", "relaxing at home"],
            )
            if occasion and st.button("Find Cocktails", type="primary"):
                with st.spinner("Mixing for the moment…"):
                    text = f"cocktail for {occasion}"
                    emb = recommender.get_user_preferences_embedding([text])
                    rows = recommender.search_similar_cocktails(emb, limit=top_k, threshold=sim_thresh)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # --- Mixed Preferences (vector-based) ---
        elif mode == "🎲 Mixed Preferences":
            st.subheader("Mix & Match")
            c1, c2 = st.columns(2)
            with c1:
                ing = st.multiselect("Ingredients", common_ingredients())
                sty = st.multiselect("Style", ["sweet", "sour", "strong", "light", "fruity", "refreshing"])
            with c2:
                occ = st.selectbox("Occasion", ["", "party", "date night", "summer", "winter", "brunch"])
                alc = st.selectbox("Alcoholic preference", ["", "Alcoholic", "Non alcoholic", "Optional alcohol"])
            if any([ing, sty, occ, alc]) and st.button("Find My Perfect Cocktail", type="primary"):
                with st.spinner("Analyzing preferences…"):
                    parts: List[str] = []
                    if ing: parts.append(f"contains {' and '.join(ing)}")
                    if sty: parts.append(f"is {' and '.join(sty)}")
                    if occ: parts.append(f"perfect for {occ}")
                    if alc: parts.append(f"is {alc}")
                    emb = recommender.get_user_preferences_embedding(parts)
                    rows = recommender.search_similar_cocktails(emb, limit=top_k, threshold=sim_thresh)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # --- By Category (non-vector) ---
        elif mode == "📂 By Category":
            st.subheader("Browse by Category")
            cat = st.selectbox(
                "Choose a category",
                ["", "Ordinary Drink", "Cocktail", "Shot", "Coffee / Tea", "Homemade Liqueur", "Punch / Party Drink", "Beer", "Soft Drink"],
            )
            if cat:
                with st.spinner("Loading category…"):
                    rows = recommender.get_cocktails_by_category(cat, limit=top_k)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # --- Random (non-vector) ---
        elif mode == "🎰 Random Discovery":
            st.subheader("Surprise Me")
            st.write("Let AI inspire you with random cocktails.")
            if st.button("🎲 Roll", type="primary"):
                with st.spinner("Shuffling…"):
                    rows = recommender.get_random_cocktails(limit=top_k)
                    st.session_state["results"] = [recommender.format_result(r) for r in rows]

        # Render results
        if st.session_state["results"]:
            st.divider()
            st.subheader(f"🍹 Found {len(st.session_state['results'])} cocktail(s)")
            render_cards(st.session_state["results"], per_row=2)

    with right:
        st.subheader("📊 Controls")
        st.caption("These affect similarity-based searches.")
        st.metric("Top-K", top_k)
        st.metric("Similarity ≥", f"{int(sim_thresh * 100)}%")
        st.caption("Raise the threshold for stricter matches; lower it for more variety.")

        st.subheader("💡 Tips")
        st.info(
            "- Be specific with ingredients\n"
            "- Combine multiple styles (e.g., *sweet* + *refreshing*)\n"
            "- Try different occasions\n"
            "- Random discovery = new ideas\n"
            "- Partial names work too!"
        )

        st.subheader("🛠️ Status")
        db_host = os.getenv("DB_HOST", "127.0.0.1")
        db_port = os.getenv("DB_PORT", "5432")
        model = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
        st.write(f"**DB**: {db_host}:{db_port}")
        st.write("**Model**:", model)


if __name__ == "__main__":
    main()
