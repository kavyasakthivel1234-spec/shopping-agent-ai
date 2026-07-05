const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");

const ProductSchema = new mongoose.Schema({
  id: { type: String, required: true },
  name: { type: String, required: true },
  price: { type: Number, default: 0 },
  brand: { type: String, default: "" },
  rating: { type: Number, default: 0 },
  reviews: { type: Number, default: 0 },
  camera: { type: String, default: "N/A" },
  battery: { type: String, default: "N/A" },
  thumbnail: { type: String, default: "" },
  link: { type: String, default: "" },
  source: { type: String, default: "Local" },
  source_type: { type: String, default: "Local" },
  data_mode: { type: String, default: "mock" },
  availability: { type: Boolean, default: true }
}, { _id: false });

const UserSchema = new mongoose.Schema({
  name: { type: String, required: true, trim: true },
  email: { type: String, required: true, unique: true, lowercase: true, trim: true },
  mobile: { type: String, required: true, unique: true, trim: true },
  password: { type: String, required: true },
  reset_token: { type: String, default: null },
  reset_token_expiry: { type: Date, default: null },
  favorites: [ProductSchema],
  createdAt: { type: Date, default: Date.now }
});

// Hash password before saving
UserSchema.pre("save", async function(next) {
  if (!this.isModified("password")) return next();
  try {
    const salt = await bcrypt.genSalt(10);
    this.password = await bcrypt.hash(this.password, salt);
    next();
  } catch (error) {
    next(error);
  }
});

// Compare password
UserSchema.methods.comparePassword = async function(candidatePassword) {
  return bcrypt.compare(candidatePassword, this.password);
};

module.exports = mongoose.model("User", UserSchema);
