import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import Hosts from '../pages/Hosts';
import HostDetails from '../pages/HostDetails';
import Alerts from '../pages/Alerts';
import DbInstances from '../pages/DbInstances';
import DbInstanceDetails from '../pages/DbInstanceDetails';
import ApmDashboard from '../pages/ApmDashboard';
import Transactions from '../pages/Transactions';
import Traces from '../pages/Traces';
import TraceDetail from '../pages/TraceDetail';
import Logs from '../pages/Logs';
import Topology from '../pages/Topology';
import Anomalies from '../pages/Anomalies';
import Diagnostics from '../pages/Diagnostics';

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
      <Route path="/apm" element={<ApmDashboard />} />
      <Route path="/apm/transactions" element={<Transactions />} />
      <Route path="/apm/traces" element={<Traces />} />
      <Route path="/apm/traces/:traceId" element={<TraceDetail />} />
      <Route path="/apm/logs" element={<Logs />} />
      <Route path="/apm/topology" element={<Topology />} />
      <Route path="/apm/anomalies" element={<Anomalies />} />
      <Route path="/apm/diagnostics" element={<Diagnostics />} />
    </Routes>
  );
}
