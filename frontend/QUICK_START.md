# Quick Start Guide

## Prerequisites

1. **Backend API Running**: Make sure your backend is running on `http://localhost:8000`
   ```bash
   cd /home/dev254/Public/Documents/Code/Agents/azure-ceo2
   uvicorn api.main:app --reload
   ```

2. **Node.js**: Ensure you have Node.js 18+ installed
   ```bash
   node --version
   ```

## Installation & Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# (Optional) Configure API URL if different from default
# Edit .env file or create it:
echo "VITE_API_URL=http://localhost:8000" > .env
```

## Running the Frontend

```bash
# Start development server
npm run dev

# The app will open at http://localhost:5173
```

## Testing the System

### 1. Test Health Check
- Open the app in your browser
- Check the top-right corner for connection status
- Should show "Connected" in green

### 2. Create Your First Campaign
1. Go to "Create Campaign" tab
2. Enter:
   - **Campaign Name**: "Welcome Campaign"
   - **Objective**: "Create a welcome email for new customers to increase engagement"
3. Click "Create Campaign"
4. Watch agents collaborate in real-time:
   - StrategyLead plans the campaign
   - DataSegmenter identifies the audience
   - ContentCreator generates content variants
   - ComplianceOfficer validates content
   - ExperimentRunner configures A/B tests

### 3. Configure Agents
1. Go to "Configuration" tab
2. Adjust agent settings:
   - Change temperature for more/less creative responses
   - Switch models (gpt-4o, gpt-4-turbo, etc.)
   - Adjust max tokens for response length
3. Click "Save Changes"

### 4. Validate Content
1. Go to "Content Validator" tab
2. Paste some marketing content
3. Click "Validate Content"
4. Review safety scores and violations

### 5. View Campaigns
1. Go to "Campaigns" tab
2. See all created campaigns
3. Filter by status or search

### 6. Analyze Experiments
1. Go to "Experiments" tab
2. Enter an experiment ID (from a completed campaign)
3. View statistical analysis and charts

## Troubleshooting

### Backend Not Connected
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in backend
- Verify `.env` file has correct `VITE_API_URL`

### Streaming Not Working
- Check browser console for errors
- Verify backend `/campaigns/stream` endpoint
- Try refreshing the page

### Build Errors
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

## Next Steps

- Customize agent configurations for your use case
- Adjust safety thresholds based on your requirements
- Integrate with your actual data sources
- Deploy to production (see README.md)

