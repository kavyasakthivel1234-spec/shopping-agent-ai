const express = require("express");
const auth = require("../middleware/auth");
const { searchAmazon, findProductById } = require("../services/serpapiService");
const groqService = require("../services/groqService");
const Chat = require("../models/Chat");

const router = express.Router();

// Mock reviews database (same as MOCK_REVIEWS in Python review_summary.py)
const MOCK_REVIEWS = {
  "sp-001": [
    "Battery is amazing, lasts all day easily",
    "Camera quality is great for the price",
    "Charging is quite slow compared to competitors",
    "Build quality feels premium",
    "Software updates are timely",
  ],
  "sp-002": [
    "Battery life is decent but not outstanding",
    "Camera produces vibrant colours",
    "Phone heats up during gaming",
    "Good value for money",
    "Charging speed is average",
  ],
  "sp-003": [
    "Camera is the standout feature – very sharp photos",
    "Battery easily lasts a full day",
    "Display is bright and vivid",
    "Occasional software lags noticed",
    "Excellent performance for the price",
  ],
  "sp-004": [
    "Best camera in this price range",
    "Battery could be better",
    "Fast charging is a big plus",
    "Slightly expensive but worth it",
  ],
  "sp-005": [
    "Great battery backup",
    "Camera is decent for everyday use",
    "Clean software experience",
    "Feels slightly bulky",
  ],
  "sp-006": [
    "Good camera and clean Android",
    "Battery life is solid",
    "Build quality could be improved",
    "Smooth performance",
  ],
  "sp-007": [
    "Reliable battery life",
    "Camera is average",
    "Budget-friendly and dependable",
    "No fast charging support",
  ],
  "sp-008": [
    "Good for basic usage",
    "Battery is satisfactory",
    "Camera is basic but functional",
    "Best in the entry segment",
  ]
};

const DEFAULT_REVIEWS = [
  "Product works as expected",
  "Battery life is acceptable",
  "Good value for the price"
];

// Helper to score a product based on requirements
function scoreProduct(product, features, targetBrand) {
  let score = 0;
  const name = (product.name || "").toLowerCase();
  const desc = (product.description || "").toLowerCase();
  const camera = (product.camera || "").toLowerCase();
  const battery = (product.battery || "").toLowerCase();

  const specsText = `${name} ${desc} ${camera} ${battery}`;

  // Feature scoring rules
  for (const feature of features) {
    const f = feature.toLowerCase().trim();
    if (f.includes("camera") || f.includes("photo") || f.includes("picture")) {
      // Good camera
      if (camera.includes("good camera") || camera.includes("50mp") || camera.includes("108mp") || camera.includes("ois")) {
        score += 10;
      }
    }
    if (f.includes("battery") || f.includes("backup") || f.includes("long lasting")) {
      // Long battery
      const mahMatch = battery.match(/(\d+)\s*mah/);
      if (mahMatch && parseInt(mahMatch[1], 10) >= 5000) {
        score += 10;
      }
    }
    if (f.includes("charge") || f.includes("charging") || f.includes("fast")) {
      if (battery.includes("fast") || name.includes("fast") || desc.includes("fast")) {
        score += 5;
      }
    }
    if (f.includes("5g")) {
      if (name.includes("5g") || desc.includes("5g")) {
        score += 5;
      }
    }
    if (f.includes("light") || f.includes("slim") || f.includes("thin")) {
      if (name.includes("light") || name.includes("slim") || desc.includes("light") || desc.includes("slim")) {
        score += 5;
      }
    }
  }

  // Brand preference scoring
  if (targetBrand) {
    const brandLower = targetBrand.toLowerCase().trim();
    const prodBrandLower = (product.brand || "").toLowerCase().trim();
    if (prodBrandLower.includes(brandLower) || name.includes(brandLower)) {
      score += 15; // significant boost for matching preferred brand
    }
  }

  // Rating bonus
  const rating = parseFloat(product.rating || 0);
  if (rating > 4.0) {
    score += Math.floor((rating - 4.0) * 20);
  }

  // Reviews volume bonus
  const reviewsCount = parseInt(product.reviews || 0, 10);
  if (reviewsCount > 1000) {
    score += 3;
  } else if (reviewsCount > 500) {
    score += 2;
  } else if (reviewsCount > 100) {
    score += 1;
  }

  return score;
}

// ---------------------------------------------------------------------------
// POST /api/recommend
// ---------------------------------------------------------------------------
router.post("/recommend", async (req, res) => {
  const { query } = req.body;
  if (!query || !query.trim()) {
    return res.status(400).json({ detail: "Query must not be empty." });
  }

  try {
    const requirements = await groqService.extractRequirements(query);
    const rawProducts = await searchAmazon(requirements);

    // Score and rank products
    const features = requirements.features || [];
    const targetBrand = requirements.brand || null;

    const scoredProducts = rawProducts.map(p => ({
      ...p,
      score: scoreProduct(p, features, targetBrand)
    })).sort((a, b) => b.score - a.score);

    const topPick = scoredProducts.length > 0 ? scoredProducts[0] : null;
    const alternatives = scoredProducts.length > 1 ? scoredProducts.slice(1) : [];

    res.json({
      requirements,
      top_pick: topPick,
      alternatives
    });
  } catch (error) {
    console.error("[ShoppingRoutes] Recommend error:", error.message);
    res.status(500).json({ detail: `Error processing recommendations: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// POST /api/compare
// ---------------------------------------------------------------------------
router.post("/compare", async (req, res) => {
  const { product1_id, product2_id } = req.body;

  if (!product1_id || !product2_id) {
    return res.status(400).json({ detail: "Both product1_id and product2_id are required." });
  }

  if (product1_id === product2_id) {
    return res.status(400).json({ detail: "product1_id and product2_id must be different." });
  }

  try {
    const product1 = await findProductById(product1_id);
    const product2 = await findProductById(product2_id);

    const comparison = await groqService.generateComparison(product1, product2);

    res.json({
      product1,
      product2,
      comparison
    });
  } catch (error) {
    console.error("[ShoppingRoutes] Compare error:", error.message);
    res.status(500).json({ detail: `Comparison failed: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// GET /api/pros-cons/:product_id
// ---------------------------------------------------------------------------
router.get("/pros-cons/:product_id", async (req, res) => {
  const { product_id } = req.params;

  try {
    const product = await findProductById(product_id);
    const result = await groqService.generateProsCons(product);

    res.json({
      product_id: product.id,
      product_name: product.name,
      pros: result.pros,
      cons: result.cons
    });
  } catch (error) {
    console.error("[ShoppingRoutes] Pros-cons error:", error.message);
    res.status(500).json({ detail: `Generating pros/cons failed: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// GET /api/reviews/:product_id/summary
// ---------------------------------------------------------------------------
router.get("/reviews/:product_id/summary", async (req, res) => {
  const { product_id } = req.params;

  try {
    let reviews = MOCK_REVIEWS[product_id];

    if (!reviews) {
      if (product_id.startsWith("amz-real")) {
        // Real product - generate dynamic reviews based on name
        const product = await findProductById(product_id);
        reviews = await groqService.generateMockReviews(product.name, product.rating);
      } else {
        reviews = DEFAULT_REVIEWS;
      }
    }

    const summary = await groqService.summariseReviews(reviews);

    res.json({
      product_id: product_id,
      review_count: reviews.length,
      liked: summary.liked,
      disliked: summary.disliked
    });
  } catch (error) {
    console.error("[ShoppingRoutes] Review summary error:", error.message);
    res.status(500).json({ detail: `Review summarization failed: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// POST /api/favorites (protected)
// ---------------------------------------------------------------------------
router.post("/favorites", auth, async (req, res) => {
  const { product } = req.body;

  if (!product || !product.id) {
    return res.status(400).json({ detail: "Product payload containing a unique id is required." });
  }

  try {
    const user = req.user;
    
    // Check if already in favorites
    const exists = user.favorites.some(f => f.id === product.id);
    if (!exists) {
      user.favorites.push(product);
      await user.save();
    }

    res.json({ message: "Added to favourites.", product });
  } catch (error) {
    console.error("[ShoppingRoutes] Add favorite error:", error.message);
    res.status(500).json({ detail: `Failed to save favorite: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// GET /api/favorites (protected)
// ---------------------------------------------------------------------------
router.get("/favorites", auth, async (req, res) => {
  try {
    res.json(req.user.favorites || []);
  } catch (error) {
    console.error("[ShoppingRoutes] Get favorites error:", error.message);
    res.status(500).json({ detail: `Failed to get favorites: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// DELETE /api/favorites/:product_id (protected)
// ---------------------------------------------------------------------------
router.delete("/favorites/:product_id", auth, async (req, res) => {
  const { product_id } = req.params;

  try {
    const user = req.user;
    const initialCount = user.favorites.length;
    
    user.favorites = user.favorites.filter(f => f.id !== product_id);
    
    if (user.favorites.length === initialCount) {
      return res.status(404).json({ detail: `Product '${product_id}' is not in your favourites.` });
    }
    
    await user.save();
    res.json({ message: "Removed from favourites." });
  } catch (error) {
    console.error("[ShoppingRoutes] Delete favorite error:", error.message);
    res.status(500).json({ detail: `Failed to remove favorite: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// GET /api/history (protected)
// ---------------------------------------------------------------------------
router.get("/history", auth, async (req, res) => {
  try {
    // Only load chats/searches associated with the logged-in user
    const chats = await Chat.find({ userId: req.user.id }).sort({ createdAt: -1 });
    res.json(chats);
  } catch (error) {
    console.error("[ShoppingRoutes] Get history error:", error.message);
    res.status(500).json({ detail: `Failed to get search history: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// DELETE /api/history (protected)
// ---------------------------------------------------------------------------
router.delete("/history", auth, async (req, res) => {
  try {
    // Only delete search history belonging to current user
    await Chat.deleteMany({ userId: req.user.id });
    res.json({ message: "Search history cleared successfully." });
  } catch (error) {
    console.error("[ShoppingRoutes] Clear history error:", error.message);
    res.status(500).json({ detail: `Failed to clear history: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// GET /api/chats (protected, load only user's chats)
// ---------------------------------------------------------------------------
router.get("/chats", auth, async (req, res) => {
  try {
    const chats = await Chat.find({ userId: req.user.id }).sort({ createdAt: -1 });
    res.json(chats);
  } catch (error) {
    console.error("[ShoppingRoutes] Get chats error:", error.message);
    res.status(500).json({ detail: `Failed to fetch chats: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// POST /api/chats (protected, save under current user ID)
// ---------------------------------------------------------------------------
router.post("/chats", auth, async (req, res) => {
  const { messages, query, confidence, top_pick, alternatives, assistant_response } = req.body;

  try {
    const chat = new Chat({
      userId: req.user.id, // Extract strictly from JWT token (req.user.id)
      messages: messages || [],
      query: query || "",
      confidence: confidence || 0,
      top_pick: top_pick || { name: "", price: 0 },
      alternatives: alternatives || [],
      assistant_response: assistant_response || ""
    });
    
    await chat.save();
    res.status(201).json(chat);
  } catch (error) {
    console.error("[ShoppingRoutes] Create chat error:", error.message);
    res.status(500).json({ detail: `Failed to create chat: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// DELETE /api/chats/:id (protected, verify ownership before delete)
// ---------------------------------------------------------------------------
router.delete("/chats/:id", auth, async (req, res) => {
  const { id } = req.params;

  try {
    const chat = await Chat.findById(id);
    if (!chat) {
      return res.status(404).json({ detail: "Chat session not found." });
    }

    // Authorization check
    if (chat.userId.toString() !== req.user.id) {
      return res.status(403).json({
        message: "Access denied"
      });
    }

    await Chat.deleteOne({ _id: id });
    res.json({ message: "Chat deleted successfully." });
  } catch (error) {
    console.error("[ShoppingRoutes] Delete chat error:", error.message);
    res.status(500).json({ detail: `Failed to delete chat: ${error.message}` });
  }
});

module.exports = router;
module.exports.scoreProduct = scoreProduct;
