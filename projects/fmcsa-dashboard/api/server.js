require('dotenv').config();
const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');

const app = express();
app.use(cors());
app.use(express.json());

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date() });
});

// Dynamic Search Route
app.get('/api/carriers', async (req, res) => {
  try {
    const { 
      minVehicles, 
      maxVehicles, 
      state, 
      minAuthorityAge,
      hasAccidents
    } = req.query;

    // Start building query
    let query = `SELECT * FROM active_leads WHERE 1=1`;
    let values = [];
    let paramCount = 1;

    // Dynamically append filters
    if (minVehicles) {
      query += ` AND power_units >= $${paramCount++}`;
      values.push(parseInt(minVehicles));
    }
    if (maxVehicles) {
      query += ` AND power_units <= $${paramCount++}`;
      values.push(parseInt(maxVehicles));
    }
    if (state) {
      query += ` AND physical_state = $${paramCount++}`;
      values.push(state.toUpperCase());
    }
    if (hasAccidents === 'false') {
      query += ` AND (total_crashes = 0 OR total_crashes IS NULL)`;
    }

    query += ` LIMIT 100;`; // Safety limit for now

    const result = await pool.query(query, values);
    res.json(result.rows);

  } catch (error) {
    console.error("Database query failed:", error);
    res.status(500).json({ error: "Internal Server Error" });
  }
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
  console.log(`FMCSA API running on port ${PORT}`);
});
