import express from "express";
import dotenv from "dotenv";
import cors from "cors";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 5001;

// Base route to test
app.get("/", (req, res) => {
  res.send("🚗 Smart Parking System Backend Running...");
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on http://localhost:${PORT}`);
});
