import streamlit as st
import pandas as pd
import json
import time

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

# --- Passcode Security Gate ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Jamir's Travel Matchmaker")
    st.caption("Made for free by Jamir for travel agents")
    
    passcode_input = st.text_input("Enter Passcode to Access App:", type="password")
    
    if st.button("Unlock Dashboard"):
        if passcode_input == "8155":
            st.session_state["authenticated"] = True
            st.success("Access Granted!")
            st.rerun()
        else:
            st.error("Incorrect Passcode. Access Denied.")
            
    st.stop()  # Stops app execution here until authenticated!

# --- Secure API Key Setup ---
# Safely checks Streamlit Secrets without raising StreamlitSecretNotFoundError
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    GEMINI_API_KEY = ""

# --- Tropical Beach Background & Custom Styling ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)), 
                    url('https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-attachment: fixed;
    }
    .title-text {
        color: #005f73;
        font-family: 'Trebuchet MS', sans-serif;
        font-weight: bold;
        margin-bottom: 0px;
    }
    .sub-text {
        color: #0a9396;
        font-size: 1.15rem;
        font-weight: 600;
        margin-top: -10px;
        margin-bottom: 25px;
    }
    .donate-card {
        background-color: rgba(255, 255, 255, 0.85);
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Header Banner ---
st.markdown("<h1 class='title-text'>✈️ Global AI Travel Agent Matchmaking Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-text'>🌴 Made for free by Jamir for travel agents</p>", unsafe_allow_html=True)

# --- Sidebar Setup ---
st.sidebar.header("🏖️ Search Filters & Setup")
st.sidebar.success("🔒 System Authorized (Passcode Active)")

selected_month = st.sidebar.selectbox("Travel Month", ["october", "november", "december", "january", "february", "march", "april", "may", "june", "july", "august", "september"])
avoid_seaweed = st.sidebar.checkbox("Strictly Avoid Seaweed / Sargassum Risk", value=True)
search_query = st.sidebar.text_area("Describe ANY Vacation Vibe or Criteria", "lovey-dovey beach spot with no seaweed, clear waters, luxury vibes")

search_button = st.sidebar.button("🤖 Search Global Destinations with AI")

# --- Cached & Retry-Protected AI Search Function ---
@st.cache_data(ttl=3600)  # Caches identical searches for 1 hour for fast performance
def generate_ai_travel_data(query, month, no_seaweed, key):
    client = genai.Client(api_key=key)
    
    prompt = f"""
    You are an expert travel agent AI. Generate 3 concise vacation spots for:
    Query: "{query}" | Month: {month} | Avoid Seaweed: {no_seaweed}

    Return ONLY a valid raw JSON object matching this structure exactly (NO Markdown):
    {{
      "destinations": [
        {{
          "name": "Destination Name, Country",
          "description": "Short 2-sentence description.",
          "highlights": ["Highlight 1", "Highlight 2"],
          "hotels": [
            {{"Hotel": "Hotel 1", "Rating": "5★", "Price/Night": "$1,000", "Vibe": "Luxury Resort"}},
            {{"Hotel": "Hotel 2", "Rating": "4★", "Price/Night": "$600", "Vibe": "Boutique Beach"}}
          ],
          "flights": [
            {{"Airline": "Airline", "Route": "JFK -> Hub", "Est. Flight Time": "6h", "Avg. Roundtrip": "$800"}}
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
        st.error("⚠️ Missing Gemini API Key! Please configure `GEMINI_API_KEY` in Streamlit Community Cloud Secrets.")
    else:
        with st.spinner("🤖 Jamir's AI is matching paradise destinations..."):
            try:
                st.session_state["results"] = generate_ai_travel_data(search_query, selected_month, avoid_seaweed, GEMINI_API_KEY)
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
            st.success(f"**{dest['name']}**")
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
                st.image("https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=800&q=80", caption=dest['name'], use_container_width=True)
            with col2:
                st.write(f"**Overview:** {dest['description']}")
                st.markdown(f"🎥 [Search Video Previews on YouTube](https://www.youtube.com/results?search_query={dest['name'].replace(' ', '+')})")
            st.write("---")
    else:
        st.info("Run an AI search to load location media previews.")

# --- HOTELS TAB ---
with tab3:
    if "results" in st.session_state and "destinations" in st.session_state["results"]:
        data = st.session_state["results"]["destinations"]
        dest_names = [d["name"] for d in data]
        selected_dest_name = st.selectbox("Select Destination for Hotels", dest_names)
        
        selected_dest_data = next((d for d in data if d["name"] == selected_dest_name), None)
        if selected_dest_data and "hotels" in selected_dest_data:
            st.dataframe(pd.DataFrame(selected_dest_data["hotels"]), use_container_width=True)
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
            st.dataframe(pd.DataFrame(selected_dest_flight_data["flights"]), use_container_width=True)
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

# --- Footer Banner ---
st.write("---")
st.caption("🌴 Travel Agent Dashboard | Made for free by Jamir")