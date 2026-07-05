const mongoose = require("mongoose");

async function connectDB() {
  try {
    const connString = process.env.MONGODB_URI;
    if (!connString) {
      throw new Error("MONGODB_URI is not defined in the environment variables.");
    }
    
    console.log("[Mongoose] Connecting to MongoDB...");
    const conn = await mongoose.connect(connString);
    console.log(`[Mongoose] Connected to MongoDB host: ${conn.connection.host}, database: ${conn.connection.name}`);
  } catch (error) {
    console.error(`[Mongoose] Error connecting to MongoDB: ${error.message}`);
    process.exit(1);
  }
}

module.exports = connectDB;
