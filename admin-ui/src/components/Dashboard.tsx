import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Call, CallDetail, AgentStatus, ApiResponse, SearchFilters, WebSocketMessage } from '../types';

const Dashboard: React.FC = () => {
  const [calls, setCalls] = useState<Call[]>([]);
  const [detail, setDetail] = useState<CallDetail | null>(null);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>({
    state: 'offline',
    active_calls: 0,
    total_calls_today: 0,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFilters>({});
  const [searchQuery, setSearchQuery] = useState<string>('');

  const token = localStorage.getItem('token');

  const handleLogout = useCallback(() => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  }, []);

  const fetchCalls = useCallback(async () => {
    if (!token) return;

    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (searchQuery) params.append('query', searchQuery);
      if (filters.from_date) params.append('from_date', filters.from_date);
      if (filters.to_date) params.append('to_date', filters.to_date);
      if (filters.status) params.append('status', filters.status);

      const response = await fetch(`/v1/calls?${params.toString()}`, {
        headers: { 'X-API-Key': token },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: ApiResponse<Call> = await response.json();
      setCalls(data.items || []);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch calls:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch calls');
      setCalls([]);
    } finally {
      setLoading(false);
    }
  }, [token, searchQuery, filters]);

  const loadDetail = useCallback(async (id: string) => {
    if (!token) return;

    try {
      const response = await fetch(`/v1/admin/conversations/${id}`, {
        headers: { 'X-API-Key': token },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: CallDetail = await response.json();
      setDetail(data);
    } catch (err) {
      console.error('Failed to fetch call detail:', err);
      setDetail(null);
    }
  }, [token]);

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/v1/admin/ws?token=${encodeURIComponent(token)}`;
    
    let ws: WebSocket;
    
    const connectWebSocket = () => {
      try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('WebSocket connected');
          setAgentStatus(prev => ({ ...prev, state: 'online' }));
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            
            switch (message.event) {
              case 'agent_state':
                setAgentStatus(message.data);
                break;
              case 'call_update':
                // Refresh calls when a call is updated
                fetchCalls();
                break;
              case 'system_alert':
                console.log('System alert:', message.data);
                break;
              default:
                console.log('Unknown WebSocket message:', message);
            }
          } catch (err) {
            console.error('Failed to parse WebSocket message:', err);
          }
        };

        ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          setAgentStatus(prev => ({ ...prev, state: 'offline' }));
          
          // Reconnect after 3 seconds if not a normal closure
          if (event.code !== 1000) {
            setTimeout(connectWebSocket, 3000);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          setAgentStatus(prev => ({ ...prev, state: 'error' }));
        };
      } catch (err) {
        console.error('Failed to create WebSocket connection:', err);
        setAgentStatus(prev => ({ ...prev, state: 'error' }));
      }
    };

    connectWebSocket();

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close(1000, 'Component unmounting');
      }
    };
  }, [token, fetchCalls]);

  // Initial load
  useEffect(() => {
    fetchCalls();
  }, [fetchCalls]);

  // Debounced search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      fetchCalls();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery, fetchCalls]);

  const filteredCalls = useMemo(() => {
    let result = [...calls];
    
    if (filters.sentiment_min !== undefined) {
      result = result.filter(call => 
        call.sentiment !== undefined && call.sentiment >= filters.sentiment_min!
      );
    }
    
    if (filters.sentiment_max !== undefined) {
      result = result.filter(call => 
        call.sentiment !== undefined && call.sentiment <= filters.sentiment_max!
      );
    }

    return result;
  }, [calls, filters]);

  const formatSentiment = (sentiment?: number): string => {
    if (sentiment === undefined || sentiment === null) return 'N/A';
    return sentiment.toFixed(2);
  };

  const formatDateTime = (dateStr: string): string => {
    return new Date(dateStr).toLocaleString();
  };

  const getStatusBadgeClass = (state: AgentStatus['state']): string => {
    return `status-badge ${state}`;
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h2>TEL3SIS Admin Dashboard</h2>
          <div className={getStatusBadgeClass(agentStatus.state)}>
            <span className="status-indicator"></span>
            {agentStatus.state}
          </div>
        </div>
        <div className="header-stats">
          <div className="stat">
            <span className="stat-label">Active Calls</span>
            <span className="stat-value">{agentStatus.active_calls}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Today's Calls</span>
            <span className="stat-value">{agentStatus.total_calls_today}</span>
          </div>
        </div>
        <div className="header-actions">
          <button onClick={() => (window.location.href = '/settings')} className="btn-secondary">
            Settings
          </button>
          <button onClick={handleLogout} className="btn-primary">
            Logout
          </button>
        </div>
      </header>

      <main className="dashboard-main">
        <div className="search-filters">
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search calls by phone number, summary..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
          
          <div className="filters">
            <select 
              value={filters.status || ''} 
              onChange={(e) => setFilters(prev => ({ 
                ...prev, 
                status: e.target.value as Call['status'] || undefined 
              }))}
              className="filter-select"
            >
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>

            <input
              type="date"
              value={filters.from_date || ''}
              onChange={(e) => setFilters(prev => ({ ...prev, from_date: e.target.value || undefined }))}
              className="filter-input"
              placeholder="From Date"
            />

            <input
              type="date"
              value={filters.to_date || ''}
              onChange={(e) => setFilters(prev => ({ ...prev, to_date: e.target.value || undefined }))}
              className="filter-input"
              placeholder="To Date"
            />

            <button 
              onClick={() => setFilters({})}
              className="btn-secondary"
            >
              Clear Filters
            </button>
          </div>
        </div>

        <div className="content-container">
          <div className="calls-panel">
            {error && (
              <div className="error-message">
                <strong>Error:</strong> {error}
                <button onClick={fetchCalls} className="btn-link">Retry</button>
              </div>
            )}

            {loading ? (
              <div className="loading">Loading calls...</div>
            ) : (
              <>
                <div className="calls-header">
                  <h3>Calls ({filteredCalls.length})</h3>
                  <button onClick={fetchCalls} className="btn-secondary" disabled={loading}>
                    Refresh
                  </button>
                </div>
                
                <ul className="call-list">
                  {filteredCalls.map((call) => (
                    <li
                      key={call.id}
                      className={`call-item ${detail?.id === call.id ? 'selected' : ''}`}
                      onClick={() => loadDetail(call.id)}
                    >
                      <div className="call-info">
                        <div className="call-numbers">
                          <strong>{call.from_number} → {call.to_number}</strong>
                          <span className={`status-tag ${call.status}`}>{call.status}</span>
                        </div>
                        <div className="call-summary">
                          {call.summary || 'No summary available'}
                        </div>
                        <div className="call-meta">
                          <span>Sentiment: {formatSentiment(call.sentiment)}</span>
                          <span>•</span>
                          <span>{formatDateTime(call.created_at)}</span>
                          {call.duration && (
                            <>
                              <span>•</span>
                              <span>{Math.round(call.duration)}s</span>
                            </>
                          )}
                        </div>
                      </div>
                    </li>
                  ))}
                  
                  {filteredCalls.length === 0 && !loading && (
                    <li className="empty-state">
                      {searchQuery || Object.keys(filters).length > 0
                        ? 'No calls match your search criteria'
                        : 'No calls found'
                      }
                    </li>
                  )}
                </ul>
              </>
            )}
          </div>

          {detail && (
            <div className="detail-panel">
              <div className="detail-header">
                <h3>Call Details</h3>
                <button 
                  onClick={() => setDetail(null)} 
                  className="btn-secondary"
                >
                  Close
                </button>
              </div>
              
              <div className="detail-content">
                <div className="detail-meta">
                  <div><strong>From:</strong> {detail.from_number}</div>
                  <div><strong>To:</strong> {detail.to_number}</div>
                  <div><strong>Status:</strong> {detail.status}</div>
                  <div><strong>Sentiment:</strong> {formatSentiment(detail.sentiment)}</div>
                  <div><strong>Created:</strong> {formatDateTime(detail.created_at)}</div>
                  {detail.duration && (
                    <div><strong>Duration:</strong> {Math.round(detail.duration)}s</div>
                  )}
                  {detail.escalation && (
                    <div className="escalation-badge">Escalated to Human</div>
                  )}
                </div>

                {detail.tool_calls && detail.tool_calls.length > 0 && (
                  <div className="tool-calls">
                    <h4>Tool Calls</h4>
                    <ul>
                      {detail.tool_calls.map((tool, index) => (
                        <li key={tool.id || index} className="tool-call">
                          <strong>{tool.tool_name}</strong>
                          <pre>{JSON.stringify(tool.arguments, null, 2)}</pre>
                          {tool.result && (
                            <div className="tool-result">
                              <strong>Result:</strong>
                              <pre>{JSON.stringify(tool.result, null, 2)}</pre>
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="transcript">
                  <h4>Transcript</h4>
                  <pre className="transcript-content">{detail.transcript}</pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Dashboard;