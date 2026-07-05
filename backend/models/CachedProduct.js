const mongoose = require("mongoose");

const CachedProductSchema = new mongoose.Schema({
  id: { type: String, required: true, unique: true },
  name: { type: String, required: true },
  price: { type: Number, default: 0 },
  brand: { type: String, default: "" },
  rating: { type: Number, default: 0 },
  reviews: { type: Number, default: 0 },
  camera: { type: String, default: "N/A" },
  battery: { type: String, default: "N/A" },
  thumbnail: { type: String, default: "" },
  link: { type: String, default: "" },
  source: { type: String, default: "Amazon" },
  source_type: { type: String, default: "Real" },
  data_mode: { type: String, default: "amazon" },
  availability: { type: Boolean, default: true },
  createdAt: { type: Date, default: Date.now, index: { expires: "7d" } } // auto-clean after 7 days
});

module.exports = mongoose.model("CachedProduct", CachedProductSchema);
