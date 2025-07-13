export default function Dashboard() {
  const handleLogout = () => {
    localStorage.removeItem('token');
    window.location.href = '/';
  };

  return (
    <div className="dashboard">
      <header>
        <h2>Admin Dashboard</h2>
        <button onClick={handleLogout}>Logout</button>
      </header>
      <main>
        <p>Welcome to TEL3SIS!</p>
      </main>
    </div>
  );
}
