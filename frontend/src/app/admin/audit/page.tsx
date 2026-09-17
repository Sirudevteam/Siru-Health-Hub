'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { getApiBase } from '@/lib/api';
import {
  FiShield,
  FiRefreshCw,
  FiFilter,
  FiCheckCircle,
  FiAlertCircle,
  FiUser,
  FiClock,
  FiAlertTriangle,
  FiKey
} from 'react-icons/fi';

interface AuditLogEntry {
  id: number;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  timestamp: string;
  result: string;
  ip_address: string;
  http_method: string;
  path: string;
  status_code: number;
}

interface AuditStats {
  total_events: number;
  success_count: number;
  failure_count: number;
  unauthorized_401_count: number;
  forbidden_403_count: number;
  actions_distribution: Record<string, number>;
}

export default function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [stats, setStats] = useState<AuditStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [filterAction, setFilterAction] = useState('');
  const [filterResult, setFilterResult] = useState('');
  const [filterUser, setFilterUser] = useState('');

  const fetchAuditData = async () => {
    setLoading(true);
    setError(null);
    try {
      const base = getApiBase();
      // Acquire admin token
      const authRes = await fetch(`${base}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' })
      });
      if (!authRes.ok) throw new Error('Authentication failed for Audit Explorer');
      const { access_token } = await authRes.json();
      const headers = { Authorization: `Bearer ${access_token}` };

      // Query params
      const params = new URLSearchParams();
      if (filterAction) params.set('action', filterAction);
      if (filterResult) params.set('result', filterResult);
      if (filterUser) params.set('user_id', filterUser);
      params.set('limit', '50');

      const [logsRes, statsRes] = await Promise.all([
        fetch(`${base}/audit/logs?${params.toString()}`, { headers }),
        fetch(`${base}/audit/stats`, { headers })
      ]);

      if (logsRes.ok) {
        const data = await logsRes.json();
        setLogs(data.logs || []);
      }
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditData();
  }, [filterAction, filterResult, filterUser]);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <nav className="flex items-center gap-2 text-sm text-gray-500 mb-2">
            <Link href="/" className="hover:text-emerald-600 transition">Home</Link>
            <span>›</span>
            <span className="text-gray-900 font-medium">Audit & Compliance</span>
          </nav>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <FiShield className="w-6 h-6" />
            </div>
            HIPAA Security & Audit Trail
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time compliance monitoring, user identity tracking, and cryptographic immutable access ledger.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchAuditData}
            disabled={loading}
            className="px-3.5 py-2 text-xs font-semibold bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition flex items-center gap-1.5 border disabled:opacity-50"
          >
            <FiRefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh Logs
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Card className="border-l-4 border-l-blue-500 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1">
              <FiShield className="w-3.5 h-3.5 text-blue-500" /> Total Audit Events
            </p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total_events}</p>
            <p className="text-[11px] text-gray-400 mt-0.5">Immutable database ledger</p>
          </Card>
          <Card className="border-l-4 border-l-emerald-500 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1">
              <FiCheckCircle className="w-3.5 h-3.5 text-emerald-500" /> Success Operations
            </p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">{stats.success_count}</p>
            <p className="text-[11px] text-gray-400 mt-0.5">
              {stats.total_events > 0 ? `${Math.round((stats.success_count / stats.total_events) * 100)}% compliance` : '100%'}
            </p>
          </Card>
          <Card className="border-l-4 border-l-amber-500 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1">
              <FiKey className="w-3.5 h-3.5 text-amber-500" /> 401 Unauthorized
            </p>
            <p className="text-2xl font-bold text-amber-600 mt-1">{stats.unauthorized_401_count}</p>
            <p className="text-[11px] text-gray-400 mt-0.5">Unauthenticated attempts</p>
          </Card>
          <Card className="border-l-4 border-l-rose-500 p-4">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider flex items-center gap-1">
              <FiAlertTriangle className="w-3.5 h-3.5 text-rose-500" /> 403 RBAC Blocks
            </p>
            <p className="text-2xl font-bold text-rose-600 mt-1">{stats.forbidden_403_count}</p>
            <p className="text-[11px] text-gray-400 mt-0.5">Forbidden permission alerts</p>
          </Card>
        </div>
      )}

      {/* Filter Bar */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-gray-700 uppercase tracking-wider">
          <FiFilter className="w-4 h-4 text-emerald-600" />
          Filter Audit Trail
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div>
            <label className="block text-gray-600 font-medium mb-1">Filter by User</label>
            <input
              type="text"
              placeholder="e.g. doctor.sharma, patient.arun"
              value={filterUser}
              onChange={(e) => setFilterUser(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-gray-800 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-gray-600 font-medium mb-1">Action Type</label>
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-2.5 py-1.5 text-gray-800 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="">All Actions</option>
              <option value="CREATE">CREATE (POST)</option>
              <option value="READ">READ (GET)</option>
              <option value="UPDATE">UPDATE (PUT)</option>
              <option value="DELETE">DELETE</option>
              <option value="SEARCH">SEARCH</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-600 font-medium mb-1">Outcome</label>
            <select
              value={filterResult}
              onChange={(e) => setFilterResult(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-2.5 py-1.5 text-gray-800 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="">All Outcomes</option>
              <option value="SUCCESS">SUCCESS (&lt; 400)</option>
              <option value="FAILURE">FAILURE (&ge; 400)</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Logs Table */}
      <Card className="overflow-hidden p-0">
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <h3 className="font-semibold text-gray-900 text-sm flex items-center gap-1.5">
            <FiClock className="w-4 h-4 text-gray-500" />
            Security Ledger Entries ({logs.length})
          </h3>
          <span className="text-xs text-gray-400">Showing newest 50 events</span>
        </div>

        {error && (
          <div className="p-4 bg-rose-50 text-rose-700 text-xs border-b border-rose-100 flex items-center gap-2">
            <FiAlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading && logs.length === 0 ? (
          <div className="p-12 text-center text-xs text-gray-500">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-emerald-600 mx-auto mb-2"></div>
            Loading audit records...
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-xs text-gray-400 italic">
            No audit records matching specified filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 text-gray-500 uppercase text-[10px] tracking-wider border-b">
                <tr>
                  <th className="py-2.5 px-4">Timestamp</th>
                  <th className="py-2.5 px-4">User</th>
                  <th className="py-2.5 px-4">Action</th>
                  <th className="py-2.5 px-4">Resource</th>
                  <th className="py-2.5 px-4">HTTP Path</th>
                  <th className="py-2.5 px-4 text-center">Status</th>
                  <th className="py-2.5 px-4 text-center">Result</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {logs.map((log) => {
                  const isSuccess = log.result === 'SUCCESS';
                  return (
                    <tr key={log.id} className="hover:bg-gray-50/75 transition">
                      <td className="py-2.5 px-4 text-gray-500 whitespace-nowrap font-mono text-[11px]">
                        {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '—'}
                      </td>
                      <td className="py-2.5 px-4 font-medium text-gray-900">
                        {log.user_id === 'Anonymous / Unauthenticated' ? (
                          <span className="text-gray-400 italic">anonymous</span>
                        ) : (
                          <span className="text-blue-600 font-mono flex items-center gap-1">
                            <FiUser className="w-3 h-3 text-blue-400" />
                            {log.user_id}
                          </span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 font-semibold text-gray-700">{log.action}</td>
                      <td className="py-2.5 px-4 text-gray-800">
                        {log.resource_type !== 'Unknown' ? (
                          <span className="bg-gray-100 px-1.5 py-0.5 rounded text-[11px] font-mono">
                            {log.resource_type}{log.resource_id ? `/${log.resource_id}` : ''}
                          </span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="py-2.5 px-4 text-gray-600 font-mono text-[11px] truncate max-w-xs" title={log.path}>
                        {log.http_method} {log.path}
                      </td>
                      <td className="py-2.5 px-4 text-center font-mono">
                        <span className={`px-1.5 py-0.5 rounded text-[11px] font-semibold ${log.status_code < 400 ? 'bg-emerald-50 text-emerald-700' : log.status_code === 401 || log.status_code === 403 ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'}`}>
                          {log.status_code}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-center">
                        <Badge variant={isSuccess ? 'green' : 'red'}>
                          {log.result}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
