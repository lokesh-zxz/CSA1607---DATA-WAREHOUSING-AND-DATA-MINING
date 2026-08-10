import { NextResponse } from 'next/server';
import pool from '@/lib/db';

export async function GET() {
  try {
    const kpiQuery = `
      SELECT 
        COUNT(order_id) as total_orders,
        SUM(revenue) as total_revenue,
        SUM(profit) as total_profit
      FROM dbt_schema.fact_orders
    `;
    const res = await pool.query(kpiQuery);
    return NextResponse.json(res.rows[0]);
  } catch (error) {
    console.error('Error fetching KPIs:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
