import { Pool } from 'pg';

const pool = new Pool({
  user: 'admin',
  password: 'adminpassword',
  host: 'localhost',
  port: 5432,
  database: 'adaptive_bi',
});

export default pool;
