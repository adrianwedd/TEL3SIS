import { Outlet, Navigate } from 'react-router-dom';

export default function App() {
  const token = localStorage.getItem('token');
  return token ? <Navigate to="/dashboard" /> : <Outlet />;
}
