import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Settings() {
  const [prompt, setPrompt] = useState('');
  const [voice, setVoice] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    fetch('/v1/admin/config', { headers: { 'X-API-Key': token } })
      .then((r) => r.json())
      .then((data) => {
        setPrompt(data.prompt || '');
        setVoice(data.voice || '');
      })
      .catch(() => {});
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    fetch('/v1/admin/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': token },
      body: JSON.stringify({ prompt, voice }),
    }).then(() => navigate('/dashboard'));
  };

  return (
    <div className="settings">
      <h2>Agent Settings</h2>
      <form onSubmit={handleSubmit} className="settings-form">
        <label>
          Prompt
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} />
        </label>
        <label>
          Voice ID
          <input value={voice} onChange={(e) => setVoice(e.target.value)} />
        </label>
        <button type="submit">Save</button>
      </form>
    </div>
  );
}
