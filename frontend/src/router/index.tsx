import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import Hosts from '../pages/Hosts';
import HostDetails from '../pages/HostDetails';
import Alerts from '../pages/Alerts';
import DbInstances from '../pages/DbInstances';
import DbInstanceDetails from '../pages/DbInstanceDetails';

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/hosts" element={<Hosts />} />
      <Route path="/hosts/:hostId" element={<HostDetails />} />
      <Route path="/alerts" element={<Alerts />} />
      <Route path="/db-instances" element={<DbInstances />} />
      <Route path="/db-instances/:instanceId" element={<DbInstanceDetails />} />
    </Routes>
  );
}
