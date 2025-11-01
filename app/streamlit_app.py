import streamlit as st
import httpx
from datetime import date, timedelta

st.set_page_config(page_title="Travel Copilot 🇫🇷", layout="wide")
st.title("🧭 Travel Planner Copilot — France")

API_BASE = "http://localhost:8000"

# ---- Status row
status_cols = st.columns(3)
with status_cols[0]:
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=3.0)
        r.raise_for_status()
        st.success("API: online")
    except Exception as e:
        st.error(f"API: offline — {e}")

with status_cols[1]:
    st.caption("Tip: If the page stays blank, hard-reload (⌘⇧R) or try another port.")

with status_cols[2]:
    st.caption("Using local API at http://localhost:8000")

st.divider()

# ---- Sidebar inputs
with st.sidebar:
    st.header("Trip Settings")
    origin = st.text_input("Origin airport/station", "CDG")
    cities_str = st.text_input("Cities (comma)", "Paris, Lyon")
    today = date.today()
    start_date = st.date_input("Start date", today + timedelta(days=14))
    end_date = st.date_input("End date", today + timedelta(days=17))
    budget = st.number_input("Budget (€)", min_value=100, max_value=20000, value=1200, step=50)
    party = st.number_input("Party size", min_value=1, max_value=10, value=1, step=1)
    pace = st.selectbox("Pace", ["slow","medium","fast"], index=1)
    interests = st.multiselect("Interests", ["food","art","history","nightlife","nature"], default=["food","art","history"])
    max_walk = st.slider("Max walking per day (km)", 2.0, 20.0, 8.0)
    lang = st.selectbox("Language", ["en","fr"], index=0)
    st.caption("Click below to plan your itinerary.")

clicked = st.button("✨ Plan Itinerary")

# ---- Main action
if clicked:
    cities = [c.strip() for c in cities_str.split(",") if c.strip()]
    if not cities:
        st.error("Please enter at least one city.")
    elif end_date <= start_date:
        st.error("End date must be after start date.")
    else:
        payload = {
            "origin": origin,
            "cities": cities,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "budget_eur": int(budget),
            "party_size": int(party),
            "pace": pace,
            "interests": interests,
            "max_walk_km_per_day": float(max_walk),
            "language": lang,
        }
        with st.spinner("Planning..."):
            try:
                r = httpx.post(f"{API_BASE}/plan", json=payload, timeout=20.0)
                r.raise_for_status()
                data = r.json()
            except httpx.HTTPStatusError as e:
                st.error(f"API error {e.response.status_code}: {e.response.text}")
                st.stop()
            except Exception as e:
                st.error(f"Request failed: {e}")
                st.stop()

        res = data.get("result", {})
        issues = data.get("issues", [])

        st.subheader("Itinerary Summary")
        st.write(res.get("summary", "Itinerary ready."))
        st.write(f"**Estimated total cost:** €{res.get('total_cost_estimate_eur', 0)}")

        days = res.get("days", [])
        if not days:
            st.warning("No day plans returned.")
        else:
            for d in days:
                with st.expander(f"{d['date']} — {d['city']}"):
                    for a in d.get("activities", []):
                        st.markdown(
                            f"- **{a['start_time']}–{a['end_time']}** · {a['title']} "
                            f"(≈ €{a['cost_eur']}) · {a['transport_mode']}"
                        )

        if res.get("citations"):
            st.caption("Sources:")
            for c in res["citations"]:
                st.write(c)

        if issues:
            st.warning("Checks: " + "; ".join(issues))
else:
    st.info("Set your trip in the sidebar, then click **Plan Itinerary**.")
