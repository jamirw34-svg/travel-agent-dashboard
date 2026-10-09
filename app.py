import streamlit as st
import pandas as pd
import json
import time
import html
import os
from urllib.parse import quote_plus, urlencode, urlparse
from urllib.request import Request, urlopen
from user_auth import authenticate_user, create_user, init_user_database

# Try importing Google GenAI SDK
try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Travel Agent Matchmaker | by Jamir",
    page_icon="🏖️",
    layout="wide"
)

# --- Shared Travel-Inspired Theme ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=DM+Serif+Display&display=swap');

    :root {
        --ink: #183638;
        --teal: #126b6b;
        --sea-glass: #d9eeea;
        --coral: #d96f52;
        --paper: #f8f3e9;
        --paper-deep: #e7e0d1;
        --line: rgba(24, 54, 56, 0.16);
        --stamp-pink: #f4c6d2;
        --stamp-rose: #d2727a;
        --stamp-gold: #d9b160;
        --ink-dark: rgba(32, 24, 20, 0.8);
    }
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        color: var(--ink);
    }
    h1, h2, h3 {
        color: var(--ink);
        font-family: 'DM Serif Display', Georgia, serif;
        font-weight: 400;
        letter-spacing: 0;
    }
    .stApp {
        background:
            radial-gradient(circle at 20% 20%, rgba(255,255,255,0.6), transparent 35%),
            radial-gradient(circle at 80% 18%, rgba(149, 135, 103, 0.12), transparent 30%),
            linear-gradient(135deg, var(--paper) 0%, var(--paper-deep) 100%);
    }
    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background:
            repeating-linear-gradient(
                0deg,
                rgba(93, 72, 52, 0.03),
                rgba(93, 72, 52, 0.03) 1px,
                transparent 1px,
                transparent 4px
            ),
            repeating-linear-gradient(
                90deg,
                rgba(255,255,255,0.12),
                rgba(255,255,255,0.12) 1px,
                transparent 1px,
                transparent 5px
            );
        opacity: 0.7;
        pointer-events: none;
    }
    [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        background: transparent;
        position: relative;
        z-index: 1;
    }
    [data-testid="stMainBlockContainer"] {
        max-width: 1440px;
        padding-top: 2.25rem;
        padding-bottom: 3rem;
    }
    [data-testid="stSidebar"] {
        background: rgba(20, 59, 61, 0.96);
        border-right: 1px solid rgba(255, 255, 255, 0.14);
    }
    [data-testid="stSidebar"] * {
        color: #f6fbf8;
    }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
        color: #d2e8df;
    }
    [data-testid="stForm"] {
        padding: 1.1rem 1.2rem;
        border: 1px solid rgba(24, 54, 56, 0.12);
        border-radius: 12px;
        background: rgba(255, 254, 250, 0.88);
        box-shadow: 0 12px 34px rgba(24, 54, 56, 0.08);
    }
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border-color: var(--line);
        border-radius: 7px;
        background: rgba(255, 254, 250, 0.94);
    }
    [data-testid="stSidebar"] [data-testid="stTextInput"] input,
    [data-testid="stSidebar"] [data-testid="stTextArea"] textarea,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] * {
        color: var(--ink) !important;
        caret-color: var(--teal);
    }
    [data-testid="stSidebar"] [data-testid="stTextArea"] textarea::placeholder {
        color: #667b79 !important;
        opacity: 1;
    }
    div.stButton > button, [data-testid="stFormSubmitButton"] button {
        min-height: 2.7rem;
        border: 0;
        border-radius: 7px;
        background: var(--coral);
        color: white;
        font-weight: 700;
        transition: background-color 160ms ease, transform 160ms ease;
    }
    div.stButton > button:hover, [data-testid="stFormSubmitButton"] button:hover {
        background: #bd583f;
        color: white;
        transform: translateY(-1px);
    }
    [data-testid="stTabs"] button[role="tab"] {
        color: var(--ink);
        font-weight: 600;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: var(--teal);
        border-bottom-color: var(--coral);
    }
    [data-testid="stImage"] img {
        border-radius: 10px;
    }
    .title-text {
        color: var(--ink);
        font-family: 'DM Serif Display', Georgia, serif;
        font-weight: 400;
        margin-bottom: 0;
    }
    .sub-text {
        color: var(--teal);
        font-size: 1.05rem;
        font-weight: 600;
        margin-top: 0.15rem;
        margin-bottom: 1.5rem;
    }
    .donate-card {
        background-color: rgba(255, 254, 250, 0.9);
        padding: 25px;
        border-radius: 10px;
        box-shadow: 0 8px 24px rgba(24, 54, 56, 0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    .travel-art {
        position: fixed;
        right: 4.5rem;
        top: 3.5rem;
        width: 420px;
        height: 330px;
        pointer-events: none;
        opacity: 0.9;
        z-index: 0;
        filter: drop-shadow(0 10px 12px rgba(57, 40, 18, 0.14));
    }
    .travel-art .trajectory {
        position: absolute;
        top: 18px;
        right: 10px;
        width: 330px;
        height: 200px;
        border: 4px dashed rgba(33, 26, 18, 0.8);
        border-radius: 50%;
        transform: rotate(-12deg);
    }
    .travel-art .trajectory::before {
        content: "";
        position: absolute;
        inset: 16px;
        border: 4px dashed rgba(33, 26, 18, 0.25);
        border-radius: 50%;
    }
    .travel-art .airplane {
        position: absolute;
        left: 12px;
        bottom: 68px;
        width: 120px;
        height: 70px;
        transform: rotate(-10deg);
    }
    .travel-art .stamp {
        position: absolute;
        width: 120px;
        height: 86px;
        border: 2px solid rgba(31, 25, 16, 0.6);
        border-radius: 12px;
        background: rgba(255, 255, 255, 0.04);
        transform: rotate(16deg);
        box-shadow: inset 0 0 0 3px rgba(255, 255, 255, 0.1);
        overflow: hidden;
    }
    .travel-art .stamp::before {
        content: "";
        position: absolute;
        inset: 10px;
        border: 2px solid rgba(31, 25, 16, 0.55);
        border-radius: 8px;
    }
    .travel-art .stamp sydney {
        display: none;
    }
    .travel-art .stamp-sydney {
        right: 135px;
        top: 62px;
        background: rgba(244, 198, 210, 0.65);
        transform: rotate(-8deg);
    }
    .travel-art .stamp-berlin {
        right: 18px;
        top: 88px;
        background: rgba(225, 95, 108, 0.42);
        transform: rotate(18deg);
    }
    .travel-art .stamp-label {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        font-size: 13px;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: rgba(35, 28, 18, 0.82);
        font-weight: 700;
        line-height: 1.2;
    }
    .travel-art .stamp-label .small {
        font-size: 10px;
        letter-spacing: 0.14em;
        display: block;
    }
    .travel-art .stamp-sydney .stamp-label {
        transform: rotate(-28deg);
    }
    .travel-art .stamp-berlin .stamp-label {
        transform: rotate(-16deg);
    }
    @media (max-width: 980px) {
        .travel-art {
            position: relative;
            right: auto;
            top: auto;
            width: min(100%, 500px);
            margin: 0 auto 1rem auto;
        }
    }
    @media (max-width: 768px) {
        .stApp {
            background-attachment: scroll;
        }
        [data-testid="stMainBlockContainer"] {
            padding: 1.25rem 1rem 2rem;
        }
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="travel-art" aria-hidden="true">
        <div class="trajectory"></div>
        <div class="stamp stamp-sydney">
            <div class="stamp-label">SYDNEY<br><span class="small">DEPARTURE</span></div>
        </div>
        <div class="stamp stamp-berlin">
            <div class="stamp-label">BERLIN<br><span class="small">ARRIVAL</span></div>
        </div>
        <svg class="airplane" viewBox="0 0 160 90" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path d="M14 47 L56 44 L82 12 L96 16 L78 47 L140 52 L154 60 L138 68 L79 55 L97 79 L82 82 L70 64 L56 76 L42 73 L53 57 L14 60 Z" fill="#201a19"/>
            <circle cx="73" cy="45" r="8" fill="#201a19" opacity="0.34"/>
        </svg>
    </div>
""", unsafe_allow_html=True)

# --- Passcode Security Gate ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    init_user_database()
    media_column, form_column = st.columns([1.1, 0.9], gap="large")
    with media_column:
        st.components.v1.html(
            """
            <div style="overflow:hidden;border-radius:12px;box-shadow:0 18px 44px rgba(24,54,56,.2);">
              <iframe src="https://giphy.com/embed/AErExHJVxRbkm5hPkB" width="100%" height="450" frameborder="0" allowfullscreen title="Travel GIF"></iframe>
            </div>
            """,
            height=470,
        )

    with form_column:
        st.markdown("<p style='color:#d96f52;font-size:.78rem;font-weight:700;text-transform:uppercase;'>Your next great escape starts here</p>", unsafe_allow_html=True)
        st.title("Jamir's Travel Matchmaker")
        st.caption("Sign in or create your travel agent account.")
        login_tab, register_tab = st.tabs(["Log in", "Register"])

        with login_tab:
            with st.form("login_form"):
                login_email = st.text_input("Email", key="login_email")
                login_password = st.text_input("Password", type="password", key="login_password")
                login_submitted = st.form_submit_button("Log in", use_container_width=True)

            if login_submitted:
                account_name = authenticate_user(login_email, login_password)
                if account_name:
                    st.session_state["authenticated"] = True
                    st.session_state["user_name"] = account_name
                    st.rerun()
                else:
                    st.error("Email or password is incorrect.")

            with st.expander("Use the existing access passcode"):
                with st.form("passcode_form"):
                    passcode_input = st.text_input("Access passcode", type="password")
                    passcode_submitted = st.form_submit_button("Unlock dashboard")
                if passcode_submitted:
                    if passcode_input == "8155":
                        st.session_state["authenticated"] = True
                        st.session_state["user_name"] = "Passcode access"
                        st.rerun()
                    else:
                        st.error("Incorrect passcode.")

        with register_tab:
            with st.form("register_form"):
                full_name = st.text_input("Full name")
                registration_email = st.text_input("Email address")
                registration_password = st.text_input("Password", type="password")
                password_confirmation = st.text_input("Confirm password", type="password")
                register_submitted = st.form_submit_button("Create account", use_container_width=True)

            if register_submitted:
                if registration_password != password_confirmation:
                    st.error("Passwords do not match.")
                else:
                    created, message = create_user(
                        full_name, registration_email, registration_password
                    )
                    (st.success if created else st.error)(message)

    st.stop()

# --- Secure API Key Setup ---
# Safely checks Streamlit Secrets without raising StreamlitSecretNotFoundError
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "") or os.environ.get("GEMINI_API_KEY", "")
except Exception:
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# --- Header Banner ---
st.markdown("<p style='color:#d96f52;font-size:.78rem;font-weight:700;text-transform:uppercase;margin-bottom:.25rem;'>Travel intelligence · worldwide</p>", unsafe_allow_html=True)
st.markdown("<h1 class='title-text'>Global Travel Matchmaker</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-text'>Thoughtful destination matches for the journeys ahead.</p>", unsafe_allow_html=True)

# --- Sidebar Setup ---
st.sidebar.header("🏖️ Search Filters & Setup")
st.sidebar.success(f"Signed in as {st.session_state.get('user_name', 'travel agent')}")
if st.sidebar.button("Log out"):
    st.session_state["authenticated"] = False
    st.session_state.pop("user_name", None)
    st.rerun()

selected_month = st.sidebar.selectbox("Travel Month", ["october", "november", "december", "january", "february", "march", "april", "may", "june", "july", "august", "september"])
avoid_seaweed = st.sidebar.checkbox("Strictly Avoid Seaweed / Sargassum Risk", value=True)
search_query = st.sidebar.text_area("Describe ANY Vacation Vibe or Criteria", "lovey-dovey beach spot with no seaweed, clear waters, luxury vibes")
departure_airport = st.sidebar.text_input("Departure city / airport", "New York (JFK)")
showcase_media_url = st.sidebar.text_input(
    "GIF / video URL",
    "https://giphy.com/gifs/travel-traveling-internships-AErExHJVxRbkm5hPkB",
)

search_button = st.sidebar.button("🤖 Search Global Destinations with AI")


@st.cache_data(ttl=86400, show_spinner=False)
def get_destination_photo(destination_name):
    params = urlencode({
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{destination_name} travel landscape",
        "gsrnamespace": 6,
        "gsrlimit": 12,
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "iiurlwidth": 1000,
        "format": "json",
    })
    request = Request(
        f"https://commons.wikimedia.org/w/api.php?{params}",
        headers={"User-Agent": "TravelAgentDashboard/1.0 (destination image lookup)"},
    )
    try:
        with urlopen(request, timeout=8) as response:
            result = json.load(response)
    except Exception:
        return None

    pages = result.get("query", {}).get("pages", {}).values()
    for page in pages:
        image_info = page.get("imageinfo", [{}])[0]
        if image_info.get("mime", "").startswith("image/") and image_info.get("thumburl"):
            try:
                image_request = Request(
                    image_info["thumburl"],
                    headers={"User-Agent": "TravelAgentDashboard/1.0 (destination image lookup)"},
                )
                with urlopen(image_request, timeout=10) as image_response:
                    if not image_response.headers.get_content_type().startswith("image/"):
                        continue
                    image_data = image_response.read(12 * 1024 * 1024 + 1)
                if len(image_data) > 12 * 1024 * 1024:
                    continue
            except Exception:
                continue
            return {
                "image": image_data,
                "source_url": image_info.get("descriptionurl", "https://commons.wikimedia.org/"),
                "title": page.get("title", "Destination photo").removeprefix("File:"),
            }
    return None


# --- Cached & Retry-Protected AI Search Function ---
@st.cache_data(ttl=3600)  # Caches identical searches for 1 hour for fast performance
def generate_ai_travel_data(query, month, no_seaweed, departure_airport, key):
    client = genai.Client(api_key=key)
    
    prompt = f"""
    You are an expert travel agent AI. Generate 3 concise vacation spots for:
    Query: "{query}" | Month: {month} | Avoid Seaweed: {no_seaweed}
    Flight departure city or airport: {departure_airport}

    For every destination, provide exactly 5 distinct hotel suggestions covering luxury,
    mid-range, and budget options, and exactly 4 distinct flight routing ideas from the
    specified departure airport. Do not claim live availability, current schedules, or
    verified prices. Hotel nightly rates and round-trip flight prices must be labeled as
    rough estimates, and flight times/routes must be presented as planning guidance.

    Return ONLY a valid raw JSON object matching this structure exactly (NO Markdown):
    {{
      "destinations": [
        {{
          "name": "Destination Name, Country",
          "description": "Short 2-sentence description.",
          "highlights": ["Highlight 1", "Highlight 2"],
          "hotels": [
                        {{"Hotel": "Hotel name", "Area": "Neighborhood or area", "Rating": "5★", "Price/Night Estimate": "$1,000 USD", "Vibe": "Luxury Resort"}}
          ],
          "flights": [
                        {{"Airline": "Suggested airline or airlines", "Route": "Origin -> Hub -> Destination", "Stops": "1 stop", "Est. Flight Time": "6h", "Avg. Roundtrip Estimate": "$800 USD"}}
          ]
        }}
      ]
    }}
    """
    
    # Retry loop with backoff to handle temporary server spikes
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            if "503" in str(e) and attempt < max_retries - 1:
                time.sleep(2 * (attempt + 1))
                continue
            raise e

# --- Search Execution ---
if search_button:
    if not GENAI_AVAILABLE:
        st.error("Please install the google-genai package by running: `pip install google-genai` in your terminal.")
    elif not GEMINI_API_KEY:
        st.error("Missing Gemini API key. Set `GEMINI_API_KEY` in `.streamlit/secrets.toml`, as an environment variable, or in your Streamlit hosting secrets.")
    else:
        with st.spinner("🤖 Jamir's AI is matching paradise destinations..."):
            try:
                st.session_state["results"] = generate_ai_travel_data(
                    search_query,
                    selected_month,
                    avoid_seaweed,
                    departure_airport,
                    GEMINI_API_KEY,
                )
            except Exception as e:
                if "503" in str(e):
                    st.warning("⏳ Google's AI servers are currently experiencing high demand. Please wait a moment and try searching again!")
                else:
                    st.error(f"Error fetching data from Gemini API: {e}")

# --- Tab Layout ---
tab_home, tab1, tab2, tab3, tab4, tab_donate = st.tabs([
    "🏠 Home & Showcase", 
    "🏖️ Destinations", 
    "📸 Photos & Media", 
    "🏨 Hotels", 
    "✈️ Flights",
    "💳 Support & Donate"
])

# --- HOME & SHOWCASE TAB ---
with tab_home:
    st.subheader("🌟 Featured Paradise Destinations")

    parsed_media_url = urlparse(showcase_media_url)
    media_extension = parsed_media_url.path.lower().rsplit(".", 1)[-1] if "." in parsed_media_url.path else ""
    giphy_id = ""
    if parsed_media_url.netloc.lower() in ("giphy.com", "www.giphy.com"):
        if parsed_media_url.path.startswith("/gifs/"):
            giphy_id = parsed_media_url.path.rsplit("-", 1)[-1]
        elif parsed_media_url.path.startswith("/embed/"):
            giphy_id = parsed_media_url.path.removeprefix("/embed/").strip("/")

    if showcase_media_url and giphy_id.isalnum():
        media_html = f"""
        <iframe src="https://giphy.com/embed/{giphy_id}" width="100%" height="450" frameborder="0" allowfullscreen title="Featured travel GIF"></iframe>
        """
        st.components.v1.html(media_html, height=470)
    elif showcase_media_url and parsed_media_url.scheme in ("http", "https") and parsed_media_url.netloc and media_extension in ("gif", "mp4", "webm"):
        safe_media_url = html.escape(showcase_media_url, quote=True)
        if media_extension == "gif":
            media_html = f"""
            <img src="{safe_media_url}" alt="Featured travel animation" style="display:block;width:100%;height:450px;object-fit:cover;">
            """
        else:
            media_html = f"""
            <video src="{safe_media_url}" autoplay muted loop playsinline controls aria-label="Featured travel video" style="display:block;width:100%;height:450px;object-fit:cover;"></video>
            """
        st.components.v1.html(media_html, height=470)
    elif showcase_media_url:
        st.error("Use a direct GIF, MP4, or WebM URL to show moving media.")
    else:
        slideshow_html = """
    <div style="max-width: 100%; border-radius: 15px; overflow: hidden; box-shadow: 0 8px 20px rgba(0,0,0,0.15);">
      <img name="slide" width="100%" height="450" style="object-fit: cover; transition: all 1s ease-in-out;">
    </div>

    <script>
    var i = 0;
    var images = [
      'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1589197331516-4d34b778b1a8?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1570077188670-e3a8d69ac5ff?auto=format&fit=crop&w=1200&q=80',
      'https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&w=1200&q=80'
    ];
    var time = 3000;

    function changeImg(){
        document.slide.src = images[i];
        if(i < images.length - 1){
            i++;
        } else {
            i = 0;
        }
        setTimeout("changeImg()", time);
    }
    window.onload = changeImg;
    </script>
    """
        st.components.v1.html(slideshow_html, height=470)
    
    if "results" in st.session_state and "destinations" in st.session_state["results"]:
        st.markdown("### Scenery from your matches")
        destinations = st.session_state["results"]["destinations"]
        photo_columns = st.columns(len(destinations))
        for column, destination in zip(photo_columns, destinations):
            with column:
                photo = get_destination_photo(destination["name"])
                if photo:
                    st.image(photo["image"], caption=destination["name"], use_container_width=True)
                    st.markdown(f"[Photo source and license]({photo['source_url']})")
                else:
                    st.caption(f"No destination photo found for {destination['name']}.")

    st.markdown("""
    ### How to Use Jamir's Travel Matchmaker:
    1. Enter any vacation vibe or requirement in the sidebar text box.
    2. Choose the planned travel month.
    3. Click **'Search Global Destinations with AI'** for instant, tailored recommendations!
    """)

# --- DESTINATIONS TAB ---
with tab1:
    if "results" in st.session_state and "destinations" in st.session_state["results"]:
        data = st.session_state["results"]["destinations"]
        st.subheader(f"AI Match Results for {selected_month.capitalize()}")
        for dest in data:
            photo = get_destination_photo(dest["name"])
            image_column, detail_column = st.columns([0.9, 1.1])
            with image_column:
                if photo:
                    st.image(photo["image"], caption=dest["name"], use_container_width=True)
                    st.markdown(f"[Photo source and license]({photo['source_url']})")
                else:
                    st.caption(f"No destination photo found for {dest['name']}.")
            with detail_column:
                st.markdown(f"### {dest['name']}")
                st.write(f"**Overview:** {dest['description']}")
                st.write(f"**Highlights:** {', '.join(dest['highlights'])}")
            st.write("---")
    else:
        st.info("👈 Enter your search query in the sidebar and click **'Search Global Destinations with AI'** to generate matches!")

# --- PHOTOS & MEDIA TAB ---
with tab2:
    if "results" in st.session_state and "destinations" in st.session_state["results"]:
        data = st.session_state["results"]["destinations"]
        st.subheader("📸 Media Previews")
        for dest in data:
            st.markdown(f"### {dest['name']}")
            col1, col2 = st.columns([1, 1])
            with col1:
                photo = get_destination_photo(dest["name"])
                if photo:
                    st.image(photo["image"], caption=dest["name"], use_container_width=True)
                    st.markdown(f"[Photo source and license]({photo['source_url']})")
                else:
                    st.caption(f"No destination photo found for {dest['name']}.")
            with col2:
                st.write(f"**Overview:** {dest['description']}")
                st.markdown(f"🎥 [Search Video Previews on YouTube](https://www.youtube.com/results?search_query={quote_plus(dest['name'] + ' travel')})")
            st.write("---")
    else:
        st.subheader("Destination Scenery")
        starter_destinations = ["Maldives", "Santorini, Greece", "Kyoto, Japan"]
        photo_columns = st.columns(len(starter_destinations))
        for column, destination_name in zip(photo_columns, starter_destinations):
            with column:
                photo = get_destination_photo(destination_name)
                if photo:
                    st.image(photo["image"], caption=destination_name, use_container_width=True)
                    st.markdown(f"[Photo source and license]({photo['source_url']})")
                else:
                    st.caption(f"No destination photo found for {destination_name}.")
        st.caption("Your destination-specific gallery appears here after an AI search.")

# --- HOTELS TAB ---
with tab3:
    if "results" in st.session_state and "destinations" in st.session_state["results"]:
        data = st.session_state["results"]["destinations"]
        dest_names = [d["name"] for d in data]
        selected_dest_name = st.selectbox("Select Destination for Hotels", dest_names)
        
        selected_dest_data = next((d for d in data if d["name"] == selected_dest_name), None)
        if selected_dest_data and "hotels" in selected_dest_data:
            photo = get_destination_photo(selected_dest_name)
            if photo:
                st.image(photo["image"], caption=selected_dest_name, use_container_width=True)
                st.markdown(f"[Photo source and license]({photo['source_url']})")
            else:
                st.caption(f"No destination photo found for {selected_dest_name}.")
            st.caption("AI-generated suggestions; nightly prices and ratings are estimates. Check current availability before booking.")
            st.dataframe(pd.DataFrame(selected_dest_data["hotels"]), use_container_width=True)
            hotel_search = quote_plus(f"hotels in {selected_dest_name}")
            st.markdown(f"[Check current hotel availability](https://www.google.com/travel/hotels?q={hotel_search})")
    else:
        st.info("Run an AI search to load hotel options.")

# --- FLIGHTS TAB ---
with tab4:
    if "results" in st.session_state and "destinations" in st.session_state["results"]:
        data = st.session_state["results"]["destinations"]
        dest_names = [d["name"] for d in data]
        selected_dest_name_flight = st.selectbox("Select Destination for Flights", dest_names, key="flight_select")
        
        selected_dest_flight_data = next((d for d in data if d["name"] == selected_dest_name_flight), None)
        if selected_dest_flight_data and "flights" in selected_dest_flight_data:
            photo = get_destination_photo(selected_dest_name_flight)
            if photo:
                st.image(photo["image"], caption=selected_dest_name_flight, use_container_width=True)
                st.markdown(f"[Photo source and license]({photo['source_url']})")
            else:
                st.caption(f"No destination photo found for {selected_dest_name_flight}.")
            st.caption("AI-generated route ideas and fare estimates; verify schedules and prices with the airline before booking.")
            st.dataframe(pd.DataFrame(selected_dest_flight_data["flights"]), use_container_width=True)
            flight_query = quote_plus(
                f"flights from {departure_airport} to {selected_dest_name_flight} in {selected_month}"
            )
            st.markdown(f"[Check current flight prices](https://www.google.com/travel/flights?q={flight_query})")
    else:
        st.info("Run an AI search to load flight routes.")

# --- DONATION TAB ---
with tab_donate:
    st.subheader("💙 Support Jamir's Travel Matchmaker")
    
    st.markdown("""
    <div class="donate-card">
        <h2>Made for free by Jamir for travel agents ✈️</h2>
        <p>If this tool helps you match clients faster and close more travel bookings, feel free to support future updates!</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.info("### 💙 Support via Venmo")
    st.write("Click the button below to open Venmo and support Jamir:")
    st.markdown("[👉 Click Here to Donate on Venmo (@jamirwasil)](https://venmo.com/u/jamirwasil)")
    st.caption("Venmo Handle: @jamirwasil")
    if "results" in st.session_state and st.session_state["results"].get("destinations"):
        featured_destination = st.session_state["results"]["destinations"][0]
        featured_photo = get_destination_photo(featured_destination["name"])
        if featured_photo:
            st.image(featured_photo["image"], caption=featured_destination["name"], use_container_width=True)
            st.markdown(f"[Photo source and license]({featured_photo['source_url']})")

# --- Footer Banner ---
st.write("---")
st.caption("🌴 Travel Agent Dashboard | Made for free by Jamir")