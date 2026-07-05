const express = require("express");
const auth = require("../middleware/auth");
const Chat = require("../models/Chat");
const { searchAmazon, findProductById } = require("../services/serpapiService");
const groqService = require("../services/groqService");
const { scoreProduct } = require("./shoppingRoutes");

const router = express.Router();

// SSE event helper
function sendSSE(res, type, data) {
  res.write(`data: ${JSON.stringify({ type, ...data })}\n\n`);
}

// POST /api/assistant (protected, handles streaming)
router.post("/assistant", auth, async (req, res) => {
  // Set headers for SSE streaming
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders();

  const query = (req.body.query || "").trim();
  if (!query) {
    sendSSE(res, "error", { message: "Query must not be empty." });
    return res.end();
  }

  const userId = req.user.id; // Extract from JWT strictly via auth middleware

  try {
    // 1. Fetch conversation history or create a new one
    let conv = await Chat.findOne({ userId }).sort({ createdAt: -1 });
    if (!conv) {
      conv = new Chat({ userId, messages: [] });
    }

    // Keep history at a reasonable limit (last 30 messages) to prevent token bloat
    if (conv.messages.length > 30) {
      conv.messages = conv.messages.slice(-30);
    }

    // 2. Query Groq AI to analyze intent and context to analyze intent and context
    const analysis = await groqService.analyzeIntentAndContext(query, conv.messages);
    console.log(`[Assistant] Intent Analysis: action=${analysis.action} | reason="${analysis.reason}"`);

    // 3. Process actions
    if (analysis.action === "chat") {
      // Small talk or greetings
      const textResponse = analysis.followUpText || "Hello! How can I assist you with your shopping today?";
      
      // Stream characters/words of static reply to mimic real streaming
      const words = textResponse.split(" ");
      for (let i = 0; i < words.length; i++) {
        sendSSE(res, "text", { text: words[i] + (i < words.length - 1 ? " " : "") });
        await new Promise(resolve => setTimeout(resolve, 30)); // slight delay
      }

      // Save messages
      conv.messages.push({ sender: "user", text: query, type: "text" });
      conv.messages.push({ sender: "assistant", text: textResponse, type: "text" });
      await conv.save();

      sendSSE(res, "done", {});
      return res.end();

    } else if (analysis.action === "ask_questions") {
      // Shopping expert needs follow-up questions
      const followUpText = analysis.followUpText || "Could you tell me what your budget is, or if you have a preferred brand?";
      
      // Stream words
      const words = followUpText.split(" ");
      for (let i = 0; i < words.length; i++) {
        sendSSE(res, "text", { text: words[i] + (i < words.length - 1 ? " " : "") });
        await new Promise(resolve => setTimeout(resolve, 30));
      }

      // Save messages
      conv.messages.push({ sender: "user", text: query, type: "text" });
      conv.messages.push({ sender: "assistant", text: followUpText, type: "text" });
      await conv.save();

      sendSSE(res, "done", {});
      return res.end();

    } else if (analysis.action === "compare") {
      // Comparison requested
      sendSSE(res, "status", { message: "Analyzing options for comparison..." });

      // Find the last recommended products from chat history to compare
      const lastShoppingMsg = [...conv.messages]
        .reverse()
        .find(m => m.type === "shopping" && m.data && m.data.top_pick);

      if (!lastShoppingMsg) {
        const msg = "Please search for products first, and then I will gladly compare them side-by-side for you!";
        sendSSE(res, "text", { text: msg });
        conv.messages.push({ sender: "user", text: query, type: "text" });
        conv.messages.push({ sender: "assistant", text: msg, type: "text" });
        await conv.save();
        sendSSE(res, "done", {});
        return res.end();
      }

      const topPick = lastShoppingMsg.data.top_pick;
      const alternatives = lastShoppingMsg.data.alternatives || [];
      const productPool = [topPick, ...alternatives];

      let p1 = productPool[0];
      let p2 = productPool[1] || productPool[0];

      // If AI extracted indices or name fragments, try to resolve them
      const target = analysis.comparisonTarget || {};
      if (target.product1_index !== undefined && productPool[target.product1_index]) {
        p1 = productPool[target.product1_index];
      }
      if (target.product2_index !== undefined && productPool[target.product2_index]) {
        p2 = productPool[target.product2_index];
      }

      if (p1.id === p2.id && productPool.length > 1) {
        // Force different products if indices match by mistake
        p2 = productPool[1];
      }

      sendSSE(res, "status", { message: `Comparing ${p1.name} and ${p2.name}...` });

      const comp = await groqService.generateComparison(p1, p2);

      const comparisonPayload = {
        product1: p1,
        product2: p2,
        comparison: comp,
        pipeline: ["ComparisonAgent"]
      };

      // Stream the comparison summary text first
      const summaryText = `### Comparison Winner: **${comp.winner}**\n\n${comp.summary}\n\nHere is the detailed side-by-side comparison table:`;
      const words = summaryText.split(" ");
      for (let i = 0; i < words.length; i++) {
        sendSSE(res, "text", { text: words[i] + (i < words.length - 1 ? " " : "") });
        await new Promise(resolve => setTimeout(resolve, 20));
      }

      // Send the structured comparison card data
      sendSSE(res, "comparison", { data: comparisonPayload });

      // Save messages
      conv.messages.push({ sender: "user", text: query, type: "text" });
      conv.messages.push({
        sender: "assistant",
        text: summaryText,
        type: "comparison",
        data: comparisonPayload
      });
      await conv.save();

      sendSSE(res, "done", {});
      return res.end();

    } else if (analysis.action === "search_products") {
      // Trigger search and shopping recommendations
      sendSSE(res, "status", { message: "Analyzing query & preferences..." });

      // Extract specific requirements
      const requirements = await groqService.extractRequirements(query);
      
      sendSSE(res, "requirements", { requirements });
      sendSSE(res, "status", { message: `Searching Amazon for "${analysis.searchQuery || query}"...` });

      // Search real products
      const rawProducts = await searchAmazon({
        ...requirements,
        category: requirements.category,
        original_query: analysis.searchQuery || query
      });

      // Score products
      const scored = rawProducts.map(p => ({
        ...p,
        score: scoreProduct(p, requirements.features || [], requirements.brand)
      })).sort((a, b) => b.score - a.score);

      if (scored.length === 0) {
        const fallbackMsg = `No matching products found on Amazon for "${query}". Try broadening your budget or description.`;
        sendSSE(res, "text", { text: fallbackMsg });
        conv.messages.push({ sender: "user", text: query, type: "text" });
        conv.messages.push({ sender: "assistant", text: fallbackMsg, type: "text" });
        await conv.save();
        sendSSE(res, "done", {});
        return res.end();
      }

      const topPick = scored[0];
      const alternatives = scored.slice(1);

      sendSSE(res, "status", { message: "Crafting expert recommendations guide..." });

      // Stream the recommendations explanation guide from Groq AI
      let completeGuideText = "";
      await groqService.generateShoppingGuideStream(
        query,
        {
          category: requirements.category,
          budget: requirements.budget,
          brand: requirements.brand,
          features: requirements.features
        },
        scored.slice(0, 5), // top 5 products for explanation context
        (textChunk) => {
          completeGuideText += textChunk;
          sendSSE(res, "text", { text: textChunk });
        }
      );

      // Generate review summary on-the-fly for the top pick
      sendSSE(res, "status", { message: "Analyzing customer reviews..." });
      let reviews = MOCK_REVIEWS[topPick.id];
      if (!reviews) {
        if (topPick.id.startsWith("amz-real")) {
          reviews = await groqService.generateMockReviews(topPick.name, topPick.rating);
        } else {
          reviews = DEFAULT_REVIEWS;
        }
      }
      const reviewSummary = await groqService.summariseReviews(reviews);

      const confidence = 0.90 + Math.random() * 0.09; // Mock confidence score around 90-99%

      // Assemble shopping response payload
      const shoppingPayload = {
        requirements: {
          category: requirements.category,
          budget: requirements.budget,
          features: requirements.features
        },
        top_pick: topPick,
        alternatives: alternatives,
        review_summary: {
          product_id: topPick.id,
          review_count: reviews.length,
          liked: reviewSummary.liked,
          disliked: reviewSummary.disliked
        },
        confidence: Number(confidence.toFixed(2)),
        pipeline: ["RequirementAgent", "RecommendationAgent", "ReviewAgent"]
      };

      // Send the final products list
      sendSSE(res, "products", { data: shoppingPayload });

      // Update active conversation
      conv.messages.push({ sender: "user", text: query, type: "text" });
      conv.messages.push({
        sender: "assistant",
        text: completeGuideText,
        type: "shopping",
        data: shoppingPayload
      });
      
      // Update values for history viewing
      conv.query = query;
      conv.confidence = shoppingPayload.confidence;
      conv.top_pick = { name: topPick.name, price: topPick.price };
      conv.alternatives = alternatives.slice(0, 3).map(a => ({ name: a.name, price: a.price }));
      conv.assistant_response = `Top pick: ${topPick.name} at ₹${topPick.price.toLocaleString("en-IN")}. ${alternatives.length} alternatives found.`;

      await conv.save();

      // Write a separate search history record to MongoDB so it renders as a distinct entry in History tab
      try {
        const historyEntry = new Chat({
          userId: userId,
          query: query,
          confidence: shoppingPayload.confidence,
          top_pick: {
            name: topPick.name,
            price: topPick.price
          },
          alternatives: alternatives.slice(0, 3).map(a => ({
            name: a.name,
            price: a.price
          })),
          assistant_response: `Top pick: ${topPick.name} at ₹${topPick.price.toLocaleString("en-IN")}. ${alternatives.length} alternatives found.`,
          messages: [{ sender: "user", text: query, type: "text" }, { sender: "assistant", text: completeGuideText, type: "shopping", data: shoppingPayload }]
        });
        await historyEntry.save();
      } catch (err) {
        console.error("[AssistantRoutes] Failed to write history:", err.message);
      }

      sendSSE(res, "done", {});
      return res.end();
    }

  } catch (error) {
    console.error("[AssistantRoutes] Error:", error.message);
    sendSSE(res, "error", { message: error.message });
    return res.end();
  }
});

// Mock review constants
const MOCK_REVIEWS = {
  "sp-001": ["Battery is amazing", "Camera is great", "Charging is slow"],
  "sp-002": ["Phone heats up during gaming", "Good value for money"],
  "sp-003": ["Camera is sharp", "Battery easily lasts a day"]
};
const DEFAULT_REVIEWS = ["Product works as expected", "Good value"];

module.exports = router;
