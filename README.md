# ✈️ Travel Concierge Agent

An intelligent, multimodal travel assistant built with the **Google Agent Development Kit (ADK)** and deployed to **Vertex AI Agent Engine**. The agent helps travelers discover destinations, plan personalized trip itineraries, lookup nearby venues, estimate itemized trip budgets, convert currencies in real-time, generate visual media (images & video clips), and maintain user preferences across sessions.

![Travel Concierge Agent Demo](./demo.gif)

---

## 🚀 Implemented Features & Google Cloud Integrations

Based on the agent implementation in `app/` and `agents-cli-manifest.yaml`, the following services and tools are fully wired up:

### 1. Persistent Long-Term Memory
- **Vertex AI Memory Bank (`PreloadMemoryTool` & `generate_memories_callback`)**: Automatically retrieves and persists user travel preferences, pace, dietary requirements, and safety/allergy constraints across separate chat sessions.

### 2. Database & Venue Catalog
- **Google Cloud Firestore (`search_destinations`, `add_destination`)**: Queries and inserts structured destination catalog documents (hotels, attractions, dining) stored in Firestore.

### 3. Geocoding & Nearby Venue Search
- **Google Maps Geocoding & Places API (`geocode_address`, `find_nearby_places`)**: Converts address strings into geographic coordinates and discovers nearby restaurants, hotels, and points of interest.

### 4. Multimodal Media Generation
- **Vertex AI Imagen / Gemini (`generate_destination_image`)**: Generates custom visual destination previews using `gemini-3.1-flash-lite-image`.
- **Vertex AI Omni Model (`generate_destination_video`)**: Generates short destination video clips using `gemini-omni-flash-preview` via the Interactions API.
- **Google Cloud Storage**: Stores generated image and video media directly in a public Cloud Storage bucket.

### 5. Rich Adaptive UI (A2UI)
- **A2UI Rendering**: Emits A2UI component surfaces (Cards, Columns, Rows, Text, Images) rendered dynamically in both ADK Web and the custom FastAPI frontend.

### 6. Budgeting & Code Execution Sandbox
- **Agent Engine Sandbox Code Executor (`AgentEngineSandboxCodeExecutor`)**: Safely executes Python code inside an isolated Vertex AI sandbox for budget calculations.
- **Trip Budget Calculator (`calculate_trip_budget`)**: Computes itemized lodging, food, activity, tax, and per-person cost breakdowns.
- **Currency Exchange (`get_exchange_rate`)**: Fetches real-time foreign exchange rates for international travel planning.

---

## 🛠️ Project Structure

```
travel-concierge-agent/
├── app/
│   ├── agent.py               # Root ADK Agent definition, callbacks, and A2UI setup
│   └── tools.py               # Tool implementations (Memory, Firestore, Maps, Media, Budget)
├── frontend/
│   ├── main.py                # FastAPI proxy connecting browser to agent via A2A protocol
│   ├── requirements.txt       # Frontend dependencies
│   └── static/
│       └── index.html         # Custom chat web UI with prompt chips & A2UI renderer
├── agents-cli-manifest.yaml   # Manifest for agents-cli deployment (accli 1.1.0)
├── demo.gif                   # Looping video demonstration
└── README.md                  # Project documentation
```

---

## 💻 Local Setup & Running Instructions

### 1. Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`) authenticated with access to Vertex AI, Firestore, and Cloud Storage.

### 2. Environment Variables
Create a `.env` file in the root directory or set the environment variables:
```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_REGION="us-east1"
export GOOGLE_MAPS_API_KEY="<YOUR_MAPS_API_KEY>"
```

### 3. Running the Agent Locally (ADK Web)
Install ADK and start the developer interface:
```bash
pip install google-adk
adk web app/
```

### 4. Running the Frontend Proxy Locally
Navigate to the `frontend/` directory and launch the FastAPI server:
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT/locations/YOUR_REGION/reasoningEngines/YOUR_ENGINE_ID"
export AGENT_DIRECTORY="app"
python main.py
```
Then open `localhost:8080` in your web browser.

---

## ☁️ Deployment Instructions

### Deploy Agent to Vertex AI Agent Engine
```bash
agents-cli deploy agent-engine app/
```

### Deploy Frontend to Cloud Run
```bash
gcloud run deploy travel-concierge-frontend \
  --source ./frontend \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/YOUR_PROJECT/locations/YOUR_REGION/reasoningEngines/YOUR_ENGINE_ID",AGENT_DIRECTORY="app"
```
