import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import Hosts from '../pages/Hosts';
import HostDetails from '../pages/HostDetails';
import Alerts from '../pages/Alerts';

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/hosts" element={<Hosts />} />
      <Route path="/hosts/:hostId" element={<HostDetails />} />
      <Route path="/alerts" element={<Alerts />} />
    </Routes>
  );
}
