require("dotenv").config();
const express = require("express");
const cors = require("cors");
const connectDB = require("./config/db");

const authRoutes = require("./routes/authRoutes");
const shoppingRoutes = require("./routes/shoppingRoutes");
const assistantRoutes = require("./routes/assistantRoutes");

const app = express();
const PORT = process.env.PORT || 8000;

// Connect to MongoDB
connectDB();

// Middleware
const allowedOrigins = process.env.ALLOWED_ORIGINS 
  ? process.env.ALLOWED_ORIGINS.split(",") 
  : ["http://localhost:5173"];

app.use(cors({
  origin: function(origin, callback) {
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);
    if (allowedOrigins.indexOf(origin) === -1) {
      const msg = "The CORS policy for this site does not allow access from the specified Origin.";
      return callback(new Error(msg), false);
    }
    return callback(null, true);
  },
  credentials: true
}));

app.use(express.json());

// Logger middleware
app.use((req, res, next) => {
  console.log(`[HTTP] ${req.method} ${req.originalUrl} - ${new Date().toISOString()}`);
  next();
});

// Health check
app.get("/health", (req, res) => {
  res.json({ status: "running", version: process.env.APP_VERSION || "4.0.0" });
});

// Mount Routes
app.use("/api/auth", authRoutes);
app.use("/api", shoppingRoutes);
app.use("/api", assistantRoutes);

// 404 Route handler
app.use((req, res, next) => {
  res.status(404).json({ detail: `Route not found: ${req.method} ${req.url}` });
});

// Global Error Handler
app.use((err, req, res, next) => {
  console.error(`[ExpressError] ${err.stack || err.message}`);
  res.status(err.status || 500).json({
    detail: err.message || "Internal server error occurred."
  });
});

// Start Server
app.listen(PORT, "0.0.0.0", () => {
  console.log(`======================================================`);
  console.log(`[Server] Express server running on http://0.0.0.0:${PORT}`);
  console.log(`[Server] Environment: ${process.env.NODE_ENV || "development"}`);
  console.log(`======================================================`);
});
