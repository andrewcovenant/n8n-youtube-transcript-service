# YouTube Transcript Microservice

A lightweight microservice that extracts transcripts from YouTube videos using the `youtube-transcript-api` Python library. This service is designed to be called from n8n workflows via HTTP requests.

## 🚀 Features

- ✅ Extract YouTube video transcripts with a simple API
- ✅ Support for multiple languages
- ✅ Detailed transcript with timing information
- ✅ Docker containerization for easy deployment
- ✅ Health check endpoint for monitoring
- ✅ Comprehensive error handling
- ✅ Lightweight (~100-200MB memory footprint)

## 📋 Tech Stack

| Technology             | Version | Purpose                              |
| ---------------------- | ------- | ------------------------------------ |
| Python                 | 3.11    | Runtime environment                  |
| FastAPI                | 0.104.1 | Web framework for API endpoints      |
| Uvicorn                | 0.24.0  | ASGI server to run FastAPI           |
| youtube-transcript-api | 0.6.1   | Library to fetch YouTube transcripts |
| Docker                 | 24.x+   | Containerization                     |
| Docker Compose         | 2.x+    | Container orchestration              |

## 📁 Project Structure

```
youtube-transcript-service/
│
├── app.py                    # Main FastAPI application
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker build instructions
├── docker-compose.yml       # Docker Compose configuration
├── .dockerignore           # Files to exclude from Docker build
├── .gitignore              # Files to exclude from Git
└── README.md               # Project documentation
```

## 🔌 API Endpoints

### 1. Health Check

Check if the service is running.

**Endpoint:** `GET /health`

**Response:**

```json
{
  "status": "healthy"
}
```

**Example:**

```bash
curl http://localhost:8000/health
```

---

### 2. Get Transcript (Simple)

Get a YouTube video transcript in a simple format.

**Endpoint:** `GET /transcript/{video_id}`

**Query Parameters:**

- `lang` (optional, default: "en") - Language code for transcript

**Response (Success):**

```json
{
  "success": true,
  "videoId": "DSIH-ol29bk",
  "transcript": "Full transcript text...",
  "hasTranscript": true
}
```

**Response (Error - 404):**

```json
{
  "success": false,
  "videoId": "DSIH-ol29bk",
  "transcript": null,
  "hasTranscript": false
}
```

**Examples:**

```bash
# English transcript (default)
curl http://localhost:8000/transcript/dQw4w9WgXcQ

# Spanish transcript
curl http://localhost:8000/transcript/dQw4w9WgXcQ?lang=es
```

---

### 3. Get Transcript (Detailed)

Get a YouTube video transcript with detailed timing information.

**Endpoint:** `POST /transcript`

**Request Body:**

```json
{
  "video_id": "DSIH-ol29bk",
  "language": "en"
}
```

**Response (Success):**

```json
{
  "success": true,
  "videoId": "DSIH-ol29bk",
  "transcript": "Full transcript text...",
  "raw": [
    {
      "text": "Hello",
      "start": 0.0,
      "duration": 1.5
    },
    {
      "text": "World",
      "start": 1.5,
      "duration": 1.2
    }
  ],
  "language": "en"
}
```

**Examples:**

```bash
curl -X POST http://localhost:8000/transcript \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ", "language": "en"}'
```

---

## 🛠️ Local Development Setup

### Prerequisites

- Python 3.11+
- pip (Python package manager)
- Docker & Docker Compose (for containerization)

### Installation Steps

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd n8n-youtube-transcript-service
   ```

2. **Create virtual environment (optional but recommended):**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the service locally:**

   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Test the service:**

   ```bash
   # Health check
   curl http://localhost:8000/health

   # Get transcript
   curl http://localhost:8000/transcript/dQw4w9WgXcQ
   ```

---

## 🐳 Docker Deployment

### Build and Run with Docker

1. **Build the Docker image:**

   ```bash
   docker build -t youtube-transcript-service .
   ```

2. **Run the container:**
   ```bash
   docker run -p 8000:8000 youtube-transcript-service
   ```

### Using Docker Compose

1. **Start the service:**

   ```bash
   docker-compose up -d
   ```

2. **View logs:**

   ```bash
   docker-compose logs -f
   ```

3. **Stop the service:**
   ```bash
   docker-compose down
   ```

---

## 🌐 Deployment Options

### Recommended Hosting Platforms

1. **Railway.app** (Free tier available)

   - Easy Docker deployment
   - Automatic HTTPS
   - Free 500 hours/month

2. **Render.com** (Free tier available)

   - Simple Docker support
   - Auto-deploy from Git
   - Free tier with some limitations

3. **Fly.io** (Free tier available)

   - Excellent for microservices
   - Global edge deployment
   - Free allowances for small apps

4. **Hostinger** (If Docker support available)

   - Traditional VPS hosting
   - Full control

5. **Any VPS with Docker**
   - DigitalOcean
   - Linode
   - AWS EC2
   - Google Cloud Platform

### Resource Requirements

- **Memory:** ~100-200MB
- **CPU:** Minimal (0.1 CPU core sufficient)
- **Storage:** ~150MB (Docker image)
- **Port:** 8000 (configurable)

---

## 🔧 Environment Variables

You can configure the service using environment variables:

| Variable    | Default | Description                                     |
| ----------- | ------- | ----------------------------------------------- |
| `PORT`      | 8000    | Server port                                     |
| `LOG_LEVEL` | info    | Logging verbosity (debug, info, warning, error) |

---

## 🔗 Integration with n8n

### Using HTTP Request Node

1. **Add an HTTP Request node** to your n8n workflow

2. **Configure the node:**

   - **Method:** GET
   - **URL:** `http://your-service-url:8000/transcript/{{ $json.videoId }}`
   - **Response Format:** JSON

3. **Extract the transcript:**
   ```javascript
   {
     {
       $json.transcript;
     }
   }
   ```

### Example n8n Workflow

```
[Trigger] → [Extract Video ID] → [HTTP Request to Service] → [Process Transcript]
```

### Sample Expression

```javascript
// Extract video ID from YouTube URL
{
  {
    $json.url.split("v=")[1].split("&")[0];
  }
}
```

---

## 🛡️ Error Handling

The service handles the following scenarios:

| Scenario                   | Response                             |
| -------------------------- | ------------------------------------ |
| ✅ Video has no transcript | Returns `hasTranscript: false` (404) |
| ✅ Invalid video ID        | Returns error response (404)         |
| ✅ Network issues          | Returns 500 error                    |
| ✅ Unsupported language    | Returns error response (404)         |
| ✅ Video unavailable       | Returns error response (404)         |

---

## 📊 API Documentation

Once the service is running, you can access the interactive API documentation:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🧪 Testing

### Quick Test Commands

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test with a valid video
curl http://localhost:8000/transcript/dQw4w9WgXcQ

# Test with Spanish language
curl http://localhost:8000/transcript/dQw4w9WgXcQ?lang=es

# Test detailed endpoint
curl -X POST http://localhost:8000/transcript \
  -H "Content-Type: application/json" \
  -d '{"video_id": "dQw4w9WgXcQ", "language": "en"}'

# Test with invalid video ID
curl http://localhost:8000/transcript/invalidID123
```

---

## 📝 Logging

The service logs important information:

- Successful transcript fetches
- Failed transcript attempts (with reason)
- Server errors
- Request information

Logs are output to stdout and can be viewed with:

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f <container-id>
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🆘 Support

If you encounter any issues or have questions:

1. Check the logs for error messages
2. Verify the YouTube video ID is correct
3. Ensure the video has transcripts available
4. Test the health endpoint to verify service is running

---

## 🚀 Quick Start Summary

```bash
# Clone and navigate
git clone <repository-url>
cd n8n-youtube-transcript-service

# Run with Docker Compose (Recommended)
docker-compose up -d

# Or run locally
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Test it
curl http://localhost:8000/transcript/dQw4w9WgXcQ
```

---

**Made with ❤️ for n8n workflows**
