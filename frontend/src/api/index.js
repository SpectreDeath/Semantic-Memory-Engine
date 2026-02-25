// API Service Layer for SME Frontend
// Uses environment variables for base URLs

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000';

class ApiService {
  constructor(baseUrl = API_URL) {
    this.baseUrl = baseUrl;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // Analysis endpoints
  async analyzeGraph(text, contextId = 'tool_lab') {
    return this.request('/api/v1/analysis/graph', {
      method: 'POST',
      body: JSON.stringify({ text, context_id: contextId }),
    });
  }

  async analyzeReport(text, contextId = 'tool_lab') {
    return this.request('/api/v1/analysis/report', {
      method: 'POST',
      body: JSON.stringify({ text, context_id: contextId }),
    });
  }

  async search(query, limit = 5) {
    return this.request('/api/v1/search', {
      method: 'POST',
      body: JSON.stringify({ query, limit }),
    });
  }

  // Connection status
  async getConnectionStatus() {
    return this.request('/api/v1/connections/status');
  }

  async updateAiProvider(providerType) {
    return this.request('/api/v1/connections/ai-provider', {
      method: 'POST',
      body: JSON.stringify({ provider_type: providerType }),
    });
  }

  // Harvester
  async ingestUrl(url, options = {}) {
    return this.request('/api/v1/ingestion/crawl', {
      method: 'POST',
      body: JSON.stringify({ url, ...options }),
    });
  }

  // Memory operations
  async queryKnowledge(concept) {
    return this.request('/api/v1/query/knowledge', {
      method: 'POST',
      body: JSON.stringify({ concept }),
    });
  }

  async saveMemory(fact, source = 'user_input') {
    return this.request('/api/v1/memory/save', {
      method: 'POST',
      body: JSON.stringify({ fact, source }),
    });
  }

  async getMemoryStats() {
    return this.request('/api/v1/memory/stats');
  }

  // Tools
  async listTools() {
    return this.request('/api/v1/tools/list');
  }

  async analyzeAuthorship(text, suspectVectorId = null) {
    return this.request('/api/v1/tools/analyze_authorship', {
      method: 'POST',
      body: JSON.stringify({ text, suspect_vector_id: suspectVectorId }),
    });
  }

  async analyzeSentiment(text) {
    return this.request('/api/v1/tools/analyze_sentiment', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  async extractEntities(text) {
    return this.request('/api/v1/tools/entity_extractor', {
      method: 'POST',
      body: JSON.stringify({ text }),
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/api/v1/health');
  }
}

// WebSocket Service for real-time updates
class WebSocketService {
  constructor(url = WS_URL) {
    this.url = url;
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect(path = '/ws/diagnostics') {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      this.socket = new WebSocket(`${this.url}${path}`);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
        this.emit('connected', {});
      };

      this.socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          this.emit('message', payload);
          
          if (payload.type) {
            this.emit(payload.type, payload.data);
          }
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        this.emit('disconnected', {});
        this.attemptReconnect(path);
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.emit('error', error);
      };
    } catch (error) {
      console.error('WebSocket connection failed:', error);
    }
  }

  attemptReconnect(path) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
        this.connect(path);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
    
    return () => this.off(event, callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => callback(data));
    }
  }

  send(data) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    }
  }
}

// Export singleton instances
export const api = new ApiService();
export const ws = new WebSocketService();

// Export for use in components
export default api;
