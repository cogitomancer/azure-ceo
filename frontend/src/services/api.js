import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const campaignAPI = {
  // Create campaign (blocking)
  createCampaign: async (campaignData) => {
    const response = await api.post('/campaigns', campaignData);
    return response.data;
  },

  // Create campaign with streaming (SSE)
  createCampaignStream: (campaignData, onMessage, onError, onComplete) => {
    let buffer = '';
    
    fetch(`${API_BASE_URL}/campaigns/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(campaignData),
    })
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        const readStream = () => {
          reader.read()
            .then(({ done, value }) => {
              if (done) {
                onComplete?.();
                return;
              }
              
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              
              // Keep the last incomplete line in buffer
              buffer = lines.pop() || '';
              
              lines.forEach(line => {
                if (line.trim() === '') return;
                
                if (line.startsWith('data: ')) {
                  try {
                    const jsonStr = line.slice(6).trim();
                    if (jsonStr) {
                      const data = JSON.parse(jsonStr);
                      if (data.event === 'agent_message') {
                        onMessage?.(data);
                      } else if (data.event === 'completed') {
                        onComplete?.(data);
                      } else if (data.event === 'error') {
                        onError?.(new Error(data.message));
                      } else if (data.event === 'started') {
                        onMessage?.({ event: 'started', campaign: data.campaign });
                      }
                    }
                  } catch (e) {
                    console.error('Error parsing SSE data:', e, 'Line:', line);
                  }
                }
              });
              
              readStream();
            })
            .catch(err => {
              onError?.(err);
            });
        };
        
        readStream();
      })
      .catch(err => {
        onError?.(err);
      });
  },

  // Get campaign details
  getCampaign: async (campaignId) => {
    const response = await api.get(`/campaigns/${campaignId}`);
    return response.data;
  },

  // List campaigns
  listCampaigns: async (status, limit = 10) => {
    const params = { limit };
    if (status) params.status = status;
    const response = await api.get('/campaigns', { params });
    return response.data;
  },
};

export const segmentAPI = {
  createSegment: async (segmentData) => {
    const response = await api.post('/segments', segmentData);
    return response.data;
  },
};

export const experimentAPI = {
  recordResults: async (experimentId, results) => {
    const response = await api.post(`/experiments/${experimentId}/results`, results);
    return response.data;
  },

  getAnalysis: async (experimentId) => {
    const response = await api.get(`/experiments/${experimentId}/analysis`);
    return response.data;
  },
};

export const contentAPI = {
  validateContent: async (content) => {
    const response = await api.post('/content/validate', { content });
    return response.data;
  },
};

export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};

export default api;

