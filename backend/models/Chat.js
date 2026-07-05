const mongoose = require("mongoose");

const MessageSchema = new mongoose.Schema({
  sender: { type: String, enum: ["user", "assistant"], required: true },
  text: { type: String, required: true },
  type: { type: String, enum: ["text", "shopping", "comparison"], default: "text" },
  data: { type: mongoose.Schema.Types.Mixed, default: null },
  timestamp: { type: Date, default: Date.now }
}, { _id: false });

const ChatSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "User",
    required: true,
    index: true
  },
  messages: [MessageSchema],
  query: { type: String, default: "" },
  confidence: { type: Number, default: 0 },
  top_pick: {
    name: { type: String, default: "" },
    price: { type: Number, default: 0 }
  },
  alternatives: [{
    name: { type: String, default: "" },
    price: { type: Number, default: 0 }
  }],
  assistant_response: { type: String, default: "" },
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model("Chat", ChatSchema);
