import axios from 'axios';

const API_BASE_URL =
    import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Log the API URL being used (helpful for debugging)
console.log('API Base URL:', API_BASE_URL);

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    timeout: 30000, // 30 second timeout
});

// Add request interceptor for debugging
api.interceptors.request.use(
    (config) => {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config.data);
        return config;
    },
    (error) => {
        console.error('[API Request Error]', error);
        return Promise.reject(error);
    }
);

// Add response interceptor for better error handling
api.interceptors.response.use(
    (response) => {
        console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.status);
        return response;
    },
    (error) => {
        // Enhanced error logging
        if (error.response) {
            // Server responded with error status
            console.error('[API Error Response]', {
                status: error.response.status,
                statusText: error.response.statusText,
                url: error.config?.url,
                data: error.response.data,
                detail: error.response.data?.detail,
                fullError: JSON.stringify(error.response.data, null, 2),
            });
        } else if (error.request) {
            // Request made but no response received
            console.error('[API Network Error]', {
                message: error.message,
                url: error.config?.url,
                baseURL: error.config?.baseURL,
                code: error.code,
            });
        } else {
            // Error setting up request
            console.error('[API Setup Error]', error.message);
        }
        return Promise.reject(error);
    }
);

export const campaignAPI = {
    // Create campaign (blocking)
    createCampaign: async(campaignData) => {
        const response = await api.post('/campaigns', campaignData);
        return response.data;
    },

    // Create campaign with streaming (SSE)
    createCampaignStream: (campaignData, onMessage, onError, onComplete) => {
        let buffer = '';
        const streamUrl = `${API_BASE_URL}/campaigns/stream`;

        console.log('[Stream] Starting SSE connection to:', streamUrl);
        console.log('[Stream] Campaign data:', campaignData);

        fetch(streamUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(campaignData),
            })
            .then(response => {
                console.log('[Stream] Response received:', {
                    status: response.status,
                    statusText: response.statusText,
                    headers: Object.fromEntries(response.headers.entries()),
                });

                if (!response.ok) {
                    // Try to get error message from response
                    return response.text().then(text => {
                        let errorMessage = `HTTP error! status: ${response.status}`;
                        try {
                            const errorData = JSON.parse(text);
                            errorMessage = errorData.detail || errorData.message || errorMessage;
                        } catch (e) {
                            if (text) errorMessage += ` - ${text}`;
                        }
                        throw new Error(errorMessage);
                    });
                }

                // Check if response body exists
                if (!response.body) {
                    throw new Error('Response body is null - server may not support streaming');
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                const readStream = () => {
                    reader.read()
                        .then(({ done, value }) => {
                            if (done) {
                                console.log('[Stream] Stream completed');
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
                                        console.error('[Stream] Error parsing SSE data:', e, 'Line:', line);
                                    }
                                }
                            });

                            readStream();
                        })
                        .catch(err => {
                            console.error('[Stream] Read error:', err);
                            onError?.(err);
                        });
                };

                readStream();
            })
            .catch(err => {
                console.error('[Stream] Fetch error:', {
                    message: err.message,
                    name: err.name,
                    stack: err.stack,
                    url: streamUrl,
                });

                // Provide more helpful error messages
                let errorMessage = err.message;
                if (err.name === 'TypeError' && err.message.includes('Failed to fetch')) {
                    errorMessage = `Cannot connect to API at ${streamUrl}. Please check:
1. Backend server is running
2. CORS is properly configured
3. Network connectivity
4. Firewall settings`;
                }

                onError?.(new Error(errorMessage));
            });
    },

    // Get campaign details
    getCampaign: async(campaignId) => {
        const response = await api.get(`/campaigns/${campaignId}`);
        return response.data;
    },

    // List campaigns
    listCampaigns: async(status, limit = 10) => {
        const params = { limit };
        if (status) params.status = status;
        const response = await api.get('/campaigns', { params });
        return response.data;
    },
};

export const segmentAPI = {
    createSegment: async(segmentData) => {
        const response = await api.post('/segments', segmentData);
        return response.data;
    },
};

export const experimentAPI = {
    recordResults: async(experimentId, results) => {
        const response = await api.post(`/experiments/${experimentId}/results`, results);
        return response.data;
    },

    getAnalysis: async(experimentId) => {
        const response = await api.get(`/experiments/${experimentId}/analysis`);
        return response.data;
    },
};

export const contentAPI = {
    validateContent: async(content) => {
        const response = await api.post('/content/validate', { content });
        return response.data;
    },
};

export const healthAPI = {
    check: async() => {
        const response = await api.get('/health');
        return response.data;
    },
};

export const companyAPI = {
    // Get current company info and summary
    getCompany: async() => {
        const response = await api.get('/company');
        return response.data;
    },

    // Get company products
    getProducts: async(limit = 20) => {
        const response = await api.get('/company/products', { params: { limit } });
        return response.data;
    },

    // Search products
    searchProducts: async(query) => {
        const response = await api.get('/company/products/search', { params: { q: query } });
        return response.data;
    },

    // Get brand rules
    getBrandRules: async() => {
        const response = await api.get('/company/brand-rules');
        return response.data;
    },

    // Get customer segments
    getCustomers: async() => {
        const response = await api.get('/company/customers');
        return response.data;
    },
};

export default api;
