import { NextResponse } from 'next/server';
import pool from '@/lib/db';

export async function GET() {
  try {
    const query = `
      SELECT 
          query, 
          calls, 
          total_exec_time / calls AS avg_exec_time_ms, 
          rows
      FROM pg_stat_statements
      WHERE calls > 0 AND query NOT ILIKE '%pg_stat_statements%'
      ORDER BY avg_exec_time_ms DESC
      LIMIT 10;
    `;
    const res = await pool.query(query);
    return NextResponse.json(res.rows);
  } catch (error) {
    console.error('Error fetching slow queries:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
