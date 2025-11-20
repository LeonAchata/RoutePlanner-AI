# 🗺️ Intelligent Route Agent with Google Maps and LangGraph

Optimal route planning system using AI that understands natural language and calculates the best visiting sequence for multiple destinations.

## 🎯 Features

- ✍️ **Natural language input**: Describe your route as you would normally speak
- 🧠 **AI with LangGraph**: Structured and traceable processing flow
- 🗺️ **Google Maps APIs**: Geocoding, Distance Matrix, and Directions
- 🔄 **TSP Optimization**: Calculates optimal order using heuristics and OR-Tools
- ⚡ **REST API with FastAPI**: Fast and automatically documented backend
- 🎨 **Simple web interface**: Vanilla HTML/CSS/JS, no frameworks

## 🏗️ Architecture

The agent uses **LangGraph** to orchestrate a 6-node flow:

```
Input → Parse → Geocode → Distance Matrix → Optimize → Directions → Format
```

Each node has a single responsibility and shares state through Pydantic models.

## 📋 Requirements

- Python 3.10+
- Google Maps API Key (with Geocoding, Distance Matrix, and Directions enabled)
- OpenAI API Key

## 🚀 Installation

### 1. Clone and setup environment

```bash
git clone <your-repo>
cd route-agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and configure your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
OPENAI_API_KEY=sk-proj-your-key-here
GOOGLE_MAPS_API_KEY=AIzaSy-your-key-here
LLM_MODEL=gpt-4o-mini
DEBUG=True
```

### 3. Verify Google Maps APIs

Make sure you have these APIs enabled in Google Cloud Console:
- ✅ Geocoding API
- ✅ Distance Matrix API
- ✅ Directions API

## 🎮 Usage

### Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

### Open the web interface

Open `public/index.html` in your browser or access:
```
http://localhost:8000/docs  # Interactive documentation
```

### Example queries

```
"I'm in downtown, want to visit shopping mall, park, and restaurant, then return home"

"Need to visit office, bank, and post office from my apartment"

"Route from airport visiting hotel, conference center, and downtown"
```

## 📁 Project Structure

```
route-agent/
├── app/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings with Pydantic
│   ├── models/
│   │   ├── state.py           # Graph state
│   │   └── schemas.py         # Request/Response models
│   ├── graph/
│   │   ├── workflow.py        # Graph definition
│   │   └── nodes/             # 6 flow nodes
│   └── services/
│       ├── google_maps.py     # Google Maps client
│       ├── llm_service.py     # OpenAI client
│       └── tsp_solver.py      # TSP algorithm
├── public/
│   └── index.html             # Web interface
├── .env                       # Environment variables
└── requirements.txt
```

## 🔧 API Endpoints

### POST /api/route

Calculates optimal route from text description.

**Request:**
```json
{
  "query": "I'm downtown, want to visit the mall and the park"
}
```

**Response:**
```json
{
  "origin": "Downtown",
  "optimized_order": ["Downtown", "Shopping Mall", "Park"],
  "total_distance_km": 12.5,
  "estimated_time_min": 35,
  "steps": [
    {
      "from": "Downtown",
      "to": "Shopping Mall",
      "distance": "8.3 km",
      "time": "22 min"
    },
    {
      "from": "Shopping Mall",
      "to": "Park",
      "distance": "4.2 km",
      "time": "13 min"
    }
  ]
}
```

### GET /health

Service health check.

## 🧪 Testing

```bash
# Install testing dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## 🎓 How It Works

### 1. Parse Input (LLM)
User writes in natural language. GPT-4o-mini extracts:
- Origin
- List of destinations
- Whether to return to start

### 2. Geocoding
Converts each location to coordinates (lat, lng) using Google Geocoding API.

### 3. Distance Matrix
Calculates NxN matrix of distances and times between all locations.

### 4. TSP Optimization
Solves the traveling salesman problem using:
- Nearest Neighbor heuristic
- 2-opt optimization
- OR-Tools for large problems (>15 nodes)

### 5. Directions
Gets detailed routes with Google Directions API for each segment.

### 6. Format Output
Validates and formats final response in structured JSON.

## 🛠️ Technologies

| Component | Technology |
|-----------|-----------|
| AI Framework | LangGraph 0.2.45 |
| LLM | OpenAI GPT-4o-mini |
| Backend | FastAPI 0.115.0 |
| Validation | Pydantic V2 |
| Maps | Google Maps Platform |
| Optimization | OR-Tools 9.11 |
| Language | Python 3.10+ |

## 🔐 Security

- Don't commit `.env` with real keys
- Use environment variables for all credentials
- Configure CORS appropriately for production
- Set rate limits on Google Maps APIs

## 📈 Future Improvements

- [ ] Cache for frequent geocodings
- [ ] Support for multiple transportation modes
- [ ] Interactive map visualization
- [ ] Export route to Google Maps
- [ ] Consider real-time traffic
- [ ] Multiple vehicles / parallel routes
- [ ] Calendar integration

## 🎯 Use Cases

- **Delivery routing**: Optimize package delivery sequences
- **Sales routes**: Plan optimal customer visit order
- **Tourist itineraries**: Create efficient sightseeing routes
- **Service calls**: Schedule technician appointments efficiently
- **Multi-stop trips**: Plan errands in optimal order
- **Fleet management**: Optimize vehicle routes
- **Food delivery**: Calculate fastest delivery paths

## 💡 Example Use Cases

### Delivery Driver
```json
{
  "query": "Starting from warehouse at 123 Main St, deliver to 5 Oak Ave, 10 Elm St, 8 Pine Rd, and return to warehouse"
}
```

### Tourist Planning
```json
{
  "query": "I'm at Central Hotel, want to visit the museum, cathedral, old town, and central park"
}
```

### Sales Representative
```json
{
  "query": "Starting from office, visit clients at Tech Corp, Design Studio, and Innovation Hub, then lunch at downtown"
}
```

## 🐛 Troubleshooting

### Error: "Geocoding failed"
- Check if location names are valid and specific
- Verify Google Maps API key has Geocoding API enabled
- Check API quota limits

### Error: "Distance Matrix error"
- Ensure Distance Matrix API is enabled
- Check if locations are accessible by the selected mode
- Verify API key permissions

### Error: "No optimization found"
- Check if all locations were successfully geocoded
- Verify distance matrix returned valid results
- Try with fewer locations (start with 3-5)

### OpenAI API errors
- Verify OPENAI_API_KEY is correct
- Check if you have available credits
- Ensure model name is correct (gpt-4o-mini)

## 🔄 API Rate Limits

Be aware of Google Maps API limits:
- **Geocoding**: 50 requests/second
- **Distance Matrix**: 100 elements/second
- **Directions**: 50 requests/second

Consider implementing caching for production use.

## 🚀 Deployment

### Docker
```bash
docker build -t route-agent:latest .
docker run -e OPENAI_API_KEY=sk-xxx \
  -e GOOGLE_MAPS_API_KEY=AIza-xxx \
  -p 8000:8000 route-agent:latest
```

### Cloud Platforms
- **Railway**: Set environment variables in dashboard
- **Heroku**: Use Config Vars for API keys
- **AWS/GCP**: Use Secrets Manager for credentials

## 📝 License

MIT

## 👤 Author

**Leon Achata**
- GitHub: [@LeonAchata](https://github.com/LeonAchata)

## 🙏 Acknowledgments

- Anthropic for Claude
- Google Maps Platform
- LangChain/LangGraph community
- OpenAI for GPT models

---

**AI-Powered Route Optimization with Natural Language - Production Ready**