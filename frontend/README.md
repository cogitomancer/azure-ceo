# Marketing Agent System - Frontend

A beautiful, enterprise-ready React frontend for the Marketing Agent System. This frontend provides an intuitive interface for creating campaigns, monitoring agent collaboration, configuring system settings, and analyzing experiment results.

## Features

- 🚀 **Real-time Campaign Creation** - Watch AI agents collaborate in real-time with streaming responses
- 📊 **Campaign Management** - View and manage all your marketing campaigns
- ⚙️ **Configuration Panel** - Adjust agent parameters, safety thresholds, and experiment settings
- 📈 **Experiment Analysis** - View statistical analysis and performance charts
- 🛡️ **Content Validator** - Validate content for safety and compliance
- 🎨 **Modern UI** - Beautiful, responsive design with Tailwind CSS
- 🔌 **No Authentication** - Start using immediately without login

## Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000` (or configure via `.env`)

## Installation

```bash
# Install dependencies
npm install

# Create .env file (optional, defaults to http://localhost:8000)
cp .env.example .env
```

## Development

```bash
# Start development server
npm run dev

# The app will be available at http://localhost:5173
```

## Building for Production

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration

Create a `.env` file in the frontend directory:

```env
VITE_API_URL=http://localhost:8000
```

## Usage

### Creating a Campaign

1. Navigate to the "Create Campaign" tab
2. Enter a campaign name and objective
3. Click "Create Campaign" to start
4. Watch agents collaborate in real-time as they:
   - Plan the campaign strategy
   - Segment the target audience
   - Create content variants
   - Validate compliance
   - Configure experiments

### Configuring Agents

1. Go to the "Configuration" tab
2. Adjust agent settings:
   - **Model**: Choose between gpt-4o, gpt-4-turbo, or gpt-3.5-turbo
   - **Temperature**: Control creativity (0 = conservative, 1 = creative)
   - **Max Tokens**: Set response length limits
3. Adjust safety thresholds and experiment settings
4. Click "Save Changes"

### Analyzing Experiments

1. Navigate to "Experiments" tab
2. Enter an experiment ID
3. View statistical analysis, charts, and recommendations

### Validating Content

1. Go to "Content Validator" tab
2. Paste your marketing content
3. Click "Validate Content"
4. Review safety scores and violations

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── CampaignCreator.jsx    # Main campaign creation interface
│   │   ├── CampaignList.jsx       # Campaign listing and management
│   │   ├── ConfigurationPanel.jsx # System configuration
│   │   ├── ExperimentAnalysis.jsx # Experiment results and charts
│   │   └── ContentValidator.jsx   # Content safety validation
│   ├── services/
│   │   └── api.js                 # API client for backend
│   ├── App.jsx                    # Main application component
│   ├── main.jsx                   # Application entry point
│   └── index.css                  # Global styles with Tailwind
├── .env.example                   # Environment variables template
└── package.json                   # Dependencies and scripts
```

## API Integration

The frontend communicates with the backend via REST API:

- `POST /campaigns` - Create campaign (blocking)
- `POST /campaigns/stream` - Create campaign with streaming
- `GET /campaigns` - List campaigns
- `GET /campaigns/:id` - Get campaign details
- `GET /experiments/:id/analysis` - Get experiment analysis
- `POST /content/validate` - Validate content
- `GET /health` - Health check

## Technologies

- **React 19** - UI framework
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Recharts** - Data visualization
- **Axios** - HTTP client

## Deployment

### Build for Production

```bash
npm run build
```

The `dist/` folder contains the production-ready static files.

### Deploy to Static Hosting

The frontend can be deployed to any static hosting service:

- **Vercel**: `vercel --prod`
- **Netlify**: `netlify deploy --prod`
- **Azure Static Web Apps**: Use Azure CLI or GitHub Actions
- **AWS S3 + CloudFront**: Upload `dist/` folder to S3

### Environment Variables

Make sure to set `VITE_API_URL` to your production backend URL in your hosting platform's environment variables.

## Troubleshooting

### Backend Connection Issues

- Verify the backend is running on the configured URL
- Check CORS settings in the backend
- Verify the health endpoint: `http://localhost:8000/health`

### Streaming Not Working

- Ensure the backend supports Server-Sent Events (SSE)
- Check browser console for errors
- Verify the `/campaigns/stream` endpoint is accessible

## License

Same as the main project.
