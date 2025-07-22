import { useEffect, useState } from 'react';

export default function Dashboard() {
  const [calls, setCalls] = useState([]);
  const [detail, setDetail] = useState(null);

  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch('/v1/calls', { headers: { 'X-API-Key': token } })
      .then((r) => r.json())
      .then((data) => setCalls(data.items || []))
      .catch(() => setCalls([]));
  }, []);

  const loadDetail = (id) => {
    const token = localStorage.getItem('token');
    fetch(`/v1/admin/conversations/${id}`, {
      headers: { 'X-API-Key': token },
    })
      .then((r) => r.json())
      .then((data) => setDetail(data))
      .catch(() => setDetail(null));
  };

  return (
    <div className="dashboard">
      <header>
        <h2>Admin Dashboard</h2>
        <div>
          <button onClick={() => (window.location.href = '/settings')}>
            Settings
          </button>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </header>
      <main>
        <div className="conversations-container">
          <ul className="conversation-list">
            {calls.map((c) => (
              <li
                key={c.id}
                className="conversation-item"
                onClick={() => loadDetail(c.id)}
              >
                <strong>
                  {c.from_number} → {c.to_number}
                </strong>
                <br />
                {c.summary || 'No summary'} ({c.sentiment !== null && c.sentiment !== undefined ? c.sentiment.toFixed(2) : 'N/A'})
              </li>
            ))}
          </ul>
          {detail && (
            <div className="conversation-detail">
              <h3>Transcript</h3>
              <p>Sentiment: {detail.sentiment !== null && detail.sentiment !== undefined ? detail.sentiment.toFixed(2) : 'N/A'}</p>
              <pre>{detail.transcript}</pre>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
