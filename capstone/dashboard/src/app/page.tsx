'use client';
import { useEffect, useState } from 'react';

type KPI = {
  total_orders: string;
  total_revenue: string;
  total_profit: string;
};

type SlowQuery = {
  query: string;
  calls: string;
  avg_exec_time_ms: string;
  rows: string;
};

export default function Dashboard() {
  const [kpis, setKpis] = useState<KPI | null>(null);
  const [slowQueries, setSlowQueries] = useState<SlowQuery[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const kpiRes = await fetch('/api/kpis');
        if (kpiRes.ok) {
          const kpiData = await kpiRes.json();
          setKpis(kpiData);
        }

        const tuneRes = await fetch('/api/self-tuning');
        if (tuneRes.ok) {
          const tuneData = await tuneRes.json();
          setSlowQueries(tuneData);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const formatCurrency = (val: string) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(Number(val));
  };

  const formatNumber = (val: string) => {
    return new Intl.NumberFormat('en-US').format(Number(val));
  };

  if (loading) {
    return <div className="dashboard-container">Loading Adaptive BI Platform...</div>;
  }

  return (
    <div className="dashboard-container">
      <header>
        <h1>Adaptive BI Platform</h1>
        <p style={{ color: 'var(--text-secondary)' }}>Executive Overview & Self-Tuning Insights</p>
      </header>

      <div className="kpi-grid">
        <div className="card">
          <h3>Total Revenue</h3>
          <div className="value">{kpis ? formatCurrency(kpis.total_revenue) : '—'}</div>
        </div>
        <div className="card">
          <h3>Total Profit</h3>
          <div className="value">{kpis ? formatCurrency(kpis.total_profit) : '—'}</div>
        </div>
        <div className="card">
          <h3>Total Orders</h3>
          <div className="value">{kpis ? formatNumber(kpis.total_orders) : '—'}</div>
        </div>
      </div>

      <h2 className="section-title">Self-Tuning Data Warehouse: Slow Queries</h2>
      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table>
          <thead>
            <tr>
              <th>Query Snippet</th>
              <th>Calls</th>
              <th>Avg Exec Time (ms)</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {slowQueries.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '2rem' }}>No slow queries detected. Database is highly optimized!</td>
              </tr>
            ) : (
              slowQueries.map((sq, i) => (
                <tr key={i}>
                  <td style={{ fontFamily: 'monospace', maxWidth: '400px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {sq.query}
                  </td>
                  <td>{sq.calls}</td>
                  <td>{Number(sq.avg_exec_time_ms).toFixed(2)}</td>
                  <td><button className="btn" onClick={() => alert('Index Optimization Scheduled!')}>Optimize</button></td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
