import streamlit as st
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError
from pymongo import MongoClient
import hashlib
from datetime import datetime
import random

# --- Configuration ---
st.set_page_config(
    page_title="MyBuddy - Mental Health Companion",
    page_icon="🤗",
    layout="wide"
)

# --- MongoDB Connection ---
@st.cache_resource
def get_mongo_client():
    """Establishes a connection to MongoDB and returns the collection object."""
    try:
        MONGO_URI = st.secrets["MONGO_URI"]
        DB_NAME = st.secrets["DB_NAME"]
        COLLECTION_NAME = st.secrets["COLLECTION_NAME"]
        client = MongoClient(MONGO_URI)
        return client[DB_NAME][COLLECTION_NAME]
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        st.stop()

users_collection = get_mongo_client()

def hash_password(password):
    """Hashes a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verifies a provided password against a stored hash."""
    return stored_password == hash_password(provided_password)

def add_to_chat_history(username, user_message, ai_response, sentiment):
    """Adds a chat interaction to the user's history."""
    chat_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_message": user_message,
        "ai_response": ai_response,
        "sentiment": sentiment
    }
    users_collection.update_one(
        {"_id": username}, 
        {"$push": {"chat_history": {"$each": [chat_entry], "$position": 0}}}
    )

def analyze_sentiment(text):
    """Analyzes the sentiment of user input using Hugging Face model."""
    try:
        # Using a sentiment analysis model
        sentiment_client = InferenceClient("cardiffnlp/twitter-roberta-base-sentiment-latest", token=HF_TOKEN)
        result = sentiment_client.text_classification(text)
        
        # Map sentiment to our categories
        sentiment_label = result[0]['label']
        confidence = result[0]['score']
        
        if sentiment_label == "LABEL_0":
            return "negative", confidence
        elif sentiment_label == "LABEL_1":
            return "neutral", confidence
        else:  # LABEL_2
            return "positive", confidence
            
    except Exception as e:
        st.error(f"Sentiment analysis failed: {e}")
        return "neutral", 0.5

# Hugging Face token
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except FileNotFoundError:
    st.error("Streamlit secrets file not found. Please create a .streamlit/secrets.toml file with your HF_TOKEN.")
    st.stop()

# Initialize the main chat client
client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=HF_TOKEN)

# --- System Prompts for Mental Health Support ---
MENTAL_HEALTH_PROMPTS = {
    "main_chat": """You are MyBuddy, a compassionate, empathetic mental health companion for students. Your role is to provide emotional support, active listening, and gentle guidance.

Key guidelines:
- Be warm, non-judgmental, and validating
- Practice active listening by reflecting feelings
- Offer practical coping strategies when appropriate
- Use encouraging and hopeful language
- Normalize their experiences
- Suggest relaxation techniques when needed
- Always remind users that professional help is available for serious concerns
- NEVER diagnose conditions or replace professional therapy

Current user sentiment: {sentiment}

Respond in a caring, conversational tone. Keep responses concise but meaningful.""",

    "crisis_support": """You are providing mental health first aid. The user may be in distress.

Priority actions:
1. Validate their feelings immediately
2. Ensure they are in a safe environment
3. Provide crisis resources (hotlines, emergency contacts)
4. Encourage connecting with trusted people
5. Offer immediate grounding techniques

Be calm, direct, and supportive. Safety is the top priority.""",

    "relaxation_tips": """Provide practical, evidence-based relaxation techniques that students can use immediately.

Include:
- Breathing exercises
- Grounding techniques
- Quick mindfulness practices
- Physical relaxation methods
- Sensory-based calming strategies

Make them easy to follow and implement quickly."""
}

# --- Relaxation Resources ---
RELAXATION_TECHNIQUES = [
    {
        "name": "Box Breathing",
        "description": "Inhale for 4 counts, hold for 4 counts, exhale for 4 counts, hold for 4 counts. Repeat 4 times.",
        "duration": "2 minutes"
    },
    {
        "name": "5-4-3-2-1 Grounding",
        "description": "Name 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, 1 thing you can taste.",
        "duration": "1 minute"
    },
    {
        "name": "Progressive Muscle Relaxation",
        "description": "Tense and then relax each muscle group from toes to head, holding tension for 5 seconds then releasing.",
        "duration": "5 minutes"
    },
    {
        "name": "Mindful Breathing",
        "description": "Focus only on your breath. When your mind wanders, gently bring attention back to breathing.",
        "duration": "3 minutes"
    }
]

CRISIS_RESOURCES = [
    "National Suicide Prevention Lifeline: 988",
    "Crisis Text Line: Text HOME to 741741",
    "Emergency Services: 911",
    "Your campus counseling center",
    "Trusted friend or family member"
]

# --- AI & UI Component Functions ---

@st.cache_data(show_spinner=False)
def generate_mental_health_response(system_prompt, user_message, sentiment):
    """Generates a mental health supportive response."""
    messages = [
        {
            "role": "system",
            "content": system_prompt.format(sentiment=sentiment),
        },
        {"role": "user", "content": user_message},
    ]

    response_text = ""
    try:
        for chunk in client.chat_completion(messages, max_tokens=1024, temperature=0.7, stream=True):
            if chunk.choices and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
    except HfHubHTTPError as e:
        if e.response.status_code == 402:
            st.error("Sorry, we've reached our monthly usage limit. Please check back later.", icon="😔")
            return "I'm currently unavailable due to technical limits. Please reach out to campus counseling services or trusted people in your life."
        st.error(f"Connection error: {e}", icon="💔")
        return "I'm having trouble responding right now. Please know that your feelings are valid and important."
    except Exception as e:
        st.error(f"Error: {e}", icon="💔")
        return "I'm here for you. If you need immediate support, please contact campus counseling or a trusted person."

    return response_text.strip()

def display_chat_interface():
    """Displays the main chat interface."""
    st.subheader("💬 Chat with MyBuddy")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Add welcome message
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hi there! I'm MyBuddy, your mental health companion. I'm here to listen and support you. How are you feeling today? 🤗",
            "sentiment": "neutral"
        })

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sentiment"):
                st.caption(f"Detected mood: {message['sentiment']}")

    # Chat input
    if prompt := st.chat_input("Share how you're feeling..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Analyze sentiment
        with st.spinner("Understanding your feelings..."):
            sentiment, confidence = analyze_sentiment(prompt)
        
        # Generate response based on sentiment
        with st.chat_message("assistant"):
            with st.spinner("MyBuddy is thinking..."):
                if sentiment == "negative" and confidence > 0.7:
                    response = generate_mental_health_response(MENTAL_HEALTH_PROMPTS["crisis_support"], prompt, sentiment)
                else:
                    response = generate_mental_health_response(MENTAL_HEALTH_PROMPTS["main_chat"], prompt, sentiment)
                
                st.markdown(response)
                st.caption(f"Detected mood: {sentiment} (confidence: {confidence:.2f})")
                
                # Add to chat history
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response,
                    "sentiment": sentiment
                })
                
                # Save to database
                add_to_chat_history(st.session_state.username, prompt, response, sentiment)

def display_relaxation_tools():
    """Displays relaxation techniques and resources."""
    st.subheader("🧘‍♀️ Relaxation & Coping Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Quick Relaxation Techniques")
        for technique in RELAXATION_TECHNIQUES:
            with st.expander(f"{technique['name']} ({technique['duration']})"):
                st.write(technique['description'])
                if st.button("Try This", key=f"try_{technique['name']}"):
                    st.success(f"Great! Starting {technique['name']}. Take a moment for yourself. 💫")
    
    with col2:
        st.markdown("### Immediate Support Resources")
        st.info("""
        **If you're in crisis or need immediate help:**
        
        Remember, you're not alone and there are people who want to help.
        """)
        
        for resource in CRISIS_RESOURCES:
            st.write(f"• {resource}")
        
        st.markdown("---")
        st.markdown("### Breathing Exercise")
        st.image("https://media.giphy.com/media/l0Exk8EUzSL0YMpZe/giphy.gif", 
                caption="Follow the circle: Breathe in as it expands, out as it contracts")

def display_mood_tracker():
    """Displays mood tracking and history."""
    st.subheader("📊 Your Mood Journey")
    
    # Simple mood check-in
    st.markdown("### How are you feeling right now?")
    
    mood_options = {
        "😢 Very Low": "very_low",
        "😔 Low": "low", 
        "😐 Neutral": "neutral",
        "🙂 Good": "good",
        "😄 Great": "great"
    }
    
    selected_mood = st.radio("Select your current mood:", list(mood_options.keys()), horizontal=True)
    
    if st.button("Check In", use_container_width=True):
        # Save mood check-in
        mood_entry = {
            "timestamp": datetime.now().isoformat(),
            "mood": mood_options[selected_mood],
            "mood_label": selected_mood
        }
        
        users_collection.update_one(
            {"_id": st.session_state.username},
            {"$push": {"mood_checkins": {"$each": [mood_entry], "$position": 0}}}
        )
        st.success(f"Thanks for checking in! Remember: all feelings are valid. 💖")

    # Display recent mood history
    st.markdown("### Recent Check-ins")
    user_data = users_collection.find_one({"_id": st.session_state.username})
    mood_history = user_data.get("mood_checkins", []) if user_data else []
    
    if mood_history:
        for i, checkin in enumerate(mood_history[:5]):  # Show last 5
            date = datetime.fromisoformat(checkin['timestamp']).strftime("%b %d, %H:%M")
            st.write(f"**{date}**: {checkin['mood_label']}")
    else:
        st.info("No mood check-ins yet. Your first check-in will appear here!")

def display_chat_history():
    """Displays past chat conversations."""
    st.header("💭 Your Conversation History")
    
    user_data = users_collection.find_one({"_id": st.session_state.username})
    chat_history = user_data.get("chat_history", []) if user_data else []
    
    if not chat_history:
        st.info("You haven't chatted with MyBuddy yet. Start a conversation in the Chat tab! 💬")
    else:
        for i, entry in enumerate(chat_history):
            with st.expander(f"Chat from {entry['timestamp']} - Mood: {entry['sentiment']}"):
                st.write("**You said:**")
                st.info(entry['user_message'])
                st.write("**MyBuddy responded:**")
                st.success(entry['ai_response'])

# --- Main App Interface ---
st.title("🤗 MyBuddy - Your Mental Health Companion")

# --- Authentication UI ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.sidebar.title("Login / Register")
    choice = st.sidebar.radio("Choose an action", ["Login", "Register"])

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if choice == "Register":
        if st.sidebar.button("Register"):
            if username and password:
                if users_collection.find_one({"_id": username}):
                    st.sidebar.error("Username already exists.")
                else:
                    users_collection.insert_one({
                        "_id": username,
                        "password": hash_password(password),
                        "chat_history": [],
                        "mood_checkins": []
                    })
                    st.sidebar.success("Registration successful! Please log in.")
            else:
                st.sidebar.warning("Please enter a username and password.")

    if choice == "Login":
        if st.sidebar.button("Login"):
            if username and password:
                user_data = users_collection.find_one({"_id": username})
                if user_data and verify_password(user_data["password"], password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.sidebar.error("Invalid username or password.")
            else:
                st.sidebar.warning("Please enter your username and password.")

    # Welcome message for non-logged in users
    st.markdown("""
    ## Welcome to MyBuddy! 🌟
    
    **Your safe space for mental wellness support**
    
    MyBuddy is here to:
    - 🤗 Provide empathetic listening and emotional support
    - 🧘 Offer practical relaxation techniques  
    - 📊 Help you track your mood patterns
    - 💫 Encourage positive mental health habits
    
    *Please login or register to begin your wellness journey.*
    """)
    
    # Emergency resources always visible
    st.markdown("---")
    st.warning("""
    **If you're in crisis or need immediate help:**
    - National Suicide Prevention Lifeline: **988**
    - Crisis Text Line: Text **HOME** to **741741**
    - Emergency Services: **911**
    - Your campus counseling center
    """)

# --- Main Application ---
if st.session_state.logged_in:
    st.sidebar.title(f"Welcome, {st.session_state.username}! 🌈")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # Emergency resources in sidebar
    st.sidebar.markdown("---")
    st.sidebar.warning("""
    **Immediate Help:**
    - Crisis Lifeline: 988
    - Text: HOME to 741741
    - Emergency: 911
    """)

    # --- Main Application Tabs ---
    chat_tab, relax_tab, mood_tab, history_tab = st.tabs([
        "💬 Chat with MyBuddy", 
        "🧘 Relaxation Tools", 
        "📊 Mood Tracker", 
        "💭 History"
    ])

    with chat_tab:
        display_chat_interface()

    with relax_tab:
        display_relaxation_tools()

    with mood_tab:
        display_mood_tracker()

    with history_tab:
        display_chat_history()