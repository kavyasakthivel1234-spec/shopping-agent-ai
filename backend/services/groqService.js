/**
 * groqService.js
 * --------------
 * AI service layer — powered by Groq API (Llama 3.3 70B).
 *
 * Replaces geminiService.js completely.
 * All public exports are identical so assistantRoutes.js requires
 * no changes other than the import path.
 */

const Groq = require("groq-sdk");

const GROQ_API_KEY = process.env.GROQ_API_KEY;
if (!GROQ_API_KEY) {
  throw new Error(
    "GROQ_API_KEY is missing. Get a free key at https://console.groq.com/keys"
  );
}

const groq      = new Groq({ apiKey: GROQ_API_KEY });
const modelName = process.env.MODEL_NAME || "llama-3.3-70b-versatile";
console.log(`[GroqService] Initialised using model: ${modelName}`);

// ─────────────────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────────────────

const SMALLTALK_PATTERNS =
  /^\s*(hi+|hello+|hey+|howdy|greetings|sup|what'?s up|how are you|how r u|good morning|good afternoon|good evening|who are you|what can you do|help me|what do you do)\s*[!?.]*\s*$/i;

const FEATURE_KEYWORDS = {
  "good camera":       ["camera", "photo", "selfie", "photography", "picture", "mp"],
  "long battery life": ["battery", "mah", "long lasting", "backup", "battery life"],
  "fast charging":     ["fast charg", "quick charg", "turbo charg"],
  "good display":      ["display", "screen", "amoled", "oled"],
  "5g":                ["5g"],
  "lightweight":       ["light", "slim", "thin", "compact"],
};

const CATEGORY_ALIASES = {
  phone: "smartphone", mobile: "smartphone", smartphone: "smartphone",
  android: "smartphone", iphone: "smartphone",
  watch: "smartwatch", smartwatch: "smartwatch", wearable: "smartwatch",
  earbuds: "headphones", earphone: "headphones", headphone: "headphones",
  headset: "headphones", earbud: "headphones",
  laptop: "laptop", notebook: "laptop",
  tab: "tablet", tablet: "tablet", ipad: "tablet",
};

// ─────────────────────────────────────────────────────────────────────────────
// Core helper — single-turn chat completion
// ─────────────────────────────────────────────────────────────────────────────

async function generate(prompt) {
  try {
    const completion = await groq.chat.completions.create({
      model:       modelName,
      messages:    [{ role: "user", content: prompt }],
      temperature: 0.7,
      max_tokens:  2048,
    });
    return completion.choices[0].message.content.trim();
  } catch (error) {
    const errStr = error.message || "";
    console.error("[GroqService] API error:", errStr);
    if (errStr.toLowerCase().includes("rate_limit") || errStr.includes("429")) {
      throw new Error("Groq API rate limit reached. Please wait a moment and try again.");
    }
    throw new Error(`Groq API call failed: ${error.message}`);
  }
}

// Streaming helper — yields text chunks via callback
async function generateStream(prompt, streamCallback) {
  try {
    const stream = await groq.chat.completions.create({
      model:       modelName,
      messages:    [{ role: "user", content: prompt }],
      temperature: 0.7,
      max_tokens:  2048,
      stream:      true,
    });

    for await (const chunk of stream) {
      const text = chunk.choices[0]?.delta?.content || "";
      if (text) streamCallback(text);
    }
  } catch (error) {
    console.error("[GroqService] Stream error:", error.message);
    throw new Error(`Groq API stream failed: ${error.message}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// JSON parser helper
// ─────────────────────────────────────────────────────────────────────────────

function parseJSON(rawText) {
  let cleaned = rawText.replace(/```(?:json)?\s*/g, "").replace(/```/g, "").trim();
  const match = cleaned.match(/\{[\s\S]*\}/);
  if (match) cleaned = match[0];
  try {
    return JSON.parse(cleaned);
  } catch (error) {
    throw new Error(`Groq returned invalid JSON: ${error.message}\nRaw: ${rawText}`);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────────────────────────────────────

function isSmalltalk(query) {
  return SMALLTALK_PATTERNS.test(query.trim());
}

async function getChatResponse(message) {
  const prompt = `You are a friendly AI shopping assistant.
Reply warmly and briefly to the user's greeting.
Mention you can help find any product — phones, clothes, shoes, laptops, and more.
Keep your reply under 3 sentences. No markdown.

User: ${message}`;
  try {
    return await generate(prompt);
  } catch {
    return "Hello! I'm your AI Shopping Assistant. I can help you find products on Amazon India. What are you looking for today?";
  }
}

async function generalChat(query, chatHistoryContext = "") {
  const prompt = `You are a friendly AI shopping assistant.
Here is the context of the current conversation:
${chatHistoryContext}

Answer the user's query naturally. No product recommendations unless specifically asked.
Keep it helpful, clear, and under 4 sentences.

User: ${query}`;
  return await generate(prompt);
}

async function extractRequirements(query) {
  const originalQuery = query.trim();
  try {
    const prompt = `You are a shopping assistant AI.
Extract the shopping requirements from the query below.
Return ONLY a valid JSON object — no explanation, no markdown, no code fences.

The JSON must have exactly these keys:
  "category" : string  — the product type the user is asking for. Be specific.
  "budget"   : number  — maximum price in INR (0 if not mentioned)
  "brand"    : string  — brand preference if specified (null if not mentioned)
  "features" : array   — list of desired feature strings (can be empty)

Query: "${query}"

Return ONLY the JSON object.`;

    const raw  = await generate(prompt);
    const data = parseJSON(raw);

    let cat = String(data.category || "").toLowerCase().trim();
    cat = CATEGORY_ALIASES[cat] || cat;

    return {
      category:       cat,
      budget:         parseFloat(data.budget || 0),
      brand:          data.brand ? String(data.brand).trim() : null,
      features:       (data.features || []).map(f => String(f).toLowerCase().trim()),
      original_query: originalQuery,
    };
  } catch (error) {
    console.warn("[GroqService] LLM extraction failed, applying rule-based fallback:", error.message);
    return ruleExtractRequirements(query);
  }
}

function ruleExtractRequirements(query) {
  const q = query.toLowerCase();
  let category = "";

  for (const [kw, canonical] of Object.entries(CATEGORY_ALIASES)) {
    if (new RegExp(`\\b${kw}\\b`, "i").test(q)) {
      category = canonical;
      break;
    }
  }

  if (!category) {
    const patterns = [
      [/\b(women'?s?\s+)?dress(?:es)?\b/i, "women dresses"],
      [/\b(men'?s?\s+)?dress(?:es)?\b/i,   "men dresses"],
      [/\b(running\s+)?shoe(?:s)?\b/i,      "running shoes"],
      [/\bsneaker(?:s)?\b/i,                "sneakers"],
      [/\bt.?shirt(?:s)?\b/i,               "t-shirts"],
      [/\bjean(?:s)?\b/i,                   "jeans"],
      [/\bkurta(?:s)?\b/i,                  "kurtas"],
      [/\bbook(?:s)?\b/i,                   "books"],
      [/\bfurniture\b/i,                    "furniture"],
      [/\bbag(?:s)?\b/i,                    "bags"],
      [/\bcooker\b/i,                       "pressure cooker"],
    ];
    for (const [regex, label] of patterns) {
      if (regex.test(q)) { category = label; break; }
    }
  }

  let budget = 0;
  const budgetPatterns = [
    /(?:under|below|upto|up to|within|less than|<)\s*[₹rs.]*\s*([\d,]+)\s*k?\b/i,
    /[₹rs.]+\s*([\d,]+)\s*k?\b/i,
    /\b([\d,]+)\s*k?\s*(?:budget|price|cost|rupees?|inr)\b/i,
    /\b(\d{3,6})\b/,
  ];
  for (const pattern of budgetPatterns) {
    const m = q.match(pattern);
    if (m) {
      let val = parseFloat(m[1].replace(/,/g, ""));
      if (m[0].toLowerCase().endsWith("k")) val *= 1000;
      budget = val;
      break;
    }
  }

  const features = [];
  for (const [label, keywords] of Object.entries(FEATURE_KEYWORDS)) {
    if (keywords.some(kw => q.includes(kw))) features.push(label);
  }

  return { category: category || "products", budget, brand: null, features, original_query: query.trim() };
}

async function generateProsCons(product) {
  const prompt = `You are a product expert.
Analyse the product below and return ONLY a valid JSON object.
No explanation, no markdown, no code fences.

Return a JSON with exactly two keys:
  "pros": array of 2-4 concise strings
  "cons": array of 2-4 concise strings

Product:
  Name    : ${product.name}
  Price   : ₹${Number(product.price).toLocaleString("en-IN")}
  Category: ${product.category || "N/A"}
  Brand   : ${product.brand || "N/A"}
  Rating  : ${product.rating || "N/A"}

Return ONLY the JSON object.`;

  try {
    const raw  = await generate(prompt);
    const data = parseJSON(raw);
    return {
      pros: (data.pros || []).map(p => String(p).trim()),
      cons: (data.cons || []).map(c => String(c).trim()),
    };
  } catch {
    return {
      pros: ["Good build quality", "Value for money"],
      cons: ["Might not satisfy advanced needs", "Limited availability"],
    };
  }
}

async function generateComparison(product1, product2) {
  const prompt = `You are a product comparison expert.
Compare the two products below and return ONLY a valid JSON object.
No explanation, no markdown, no code fences.

Keys required:
  "camera"  : {"product1": "...", "product2": "..."}
  "battery" : {"product1": "...", "product2": "..."}
  "price"   : {"product1": "₹${Number(product1.price).toLocaleString("en-IN")}", "product2": "₹${Number(product2.price).toLocaleString("en-IN")}"}
  "winner"  : string — full product name of the better choice
  "summary" : string — one or two sentences explaining why

Product 1: ${product1.name} — ₹${Number(product1.price).toLocaleString("en-IN")}
Product 2: ${product2.name} — ₹${Number(product2.price).toLocaleString("en-IN")}

Return ONLY the JSON object.`;

  try {
    const raw  = await generate(prompt);
    const data = parseJSON(raw);
    return {
      camera:  data.camera  || { product1: product1.camera,  product2: product2.camera },
      battery: data.battery || { product1: product1.battery, product2: product2.battery },
      price:   data.price   || { product1: `₹${product1.price}`, product2: `₹${product2.price}` },
      winner:  data.winner  || product1.name,
      summary: data.summary || "Comparison based on available specifications.",
    };
  } catch {
    return {
      camera:  { product1: product1.camera,  product2: product2.camera },
      battery: { product1: product1.battery, product2: product2.battery },
      price:   { product1: `₹${product1.price}`, product2: `₹${product2.price}` },
      winner:  product1.name,
      summary: "Comparison completed based on default specifications.",
    };
  }
}

async function summariseReviews(reviews) {
  const reviewsText = reviews.map(r => `- ${r}`).join("\n");
  const prompt = `You are a product review analyst.
Read the reviews and return ONLY a valid JSON object. No markdown.

Keys:
  "liked"    : array of short topic strings (1-3 words)
  "disliked" : array of short topic strings (1-3 words)

Reviews:
${reviewsText}

Return ONLY the JSON object.`;

  try {
    const raw  = await generate(prompt);
    const data = parseJSON(raw);
    return {
      liked:    (data.liked    || []).map(t => String(t).trim()),
      disliked: (data.disliked || []).map(t => String(t).trim()),
    };
  } catch {
    return { liked: ["Performance", "Design"], disliked: ["Average battery"] };
  }
}

async function generateMockReviews(productName, rating) {
  const prompt = `Analyse this product: "${productName}" (Rating: ${rating || 4.2}/5).
Generate 5 realistic, short user reviews representing customer opinions.
Provide a mixture of positive and negative reviews reflecting the rating.
Return ONLY a JSON array of strings. No explanation.

Example: ["Liked the display", "Battery life is below average", "Feels lightweight"]`;

  try {
    const raw = await generate(prompt);
    const arr = parseJSON(raw);
    if (Array.isArray(arr)) return arr;
  } catch (err) {
    console.error("[GroqService] Mock reviews generation failed:", err.message);
  }
  return [
    "Product matches description. Works fine.",
    "Great value for the price.",
    "Performance is satisfactory.",
    "Build quality feels average but acceptable.",
  ];
}

async function analyzeIntentAndContext(query, historyMessages) {
  const historyText = historyMessages
    .map(m => `${m.sender.toUpperCase()}: ${m.text}`)
    .join("\n");

  const prompt = `You are the core intelligence of a premium AI Shopping Assistant.
Analyze the user's latest message and the conversation history to make a routing decision.

Available actions:
1. "chat"            — greetings, small-talk, or non-product requests
2. "compare"         — user wants to compare products already recommended
3. "ask_questions"   — user wants to buy something but lacks budget/brand/use-case details
4. "search_products" — enough info provided, or explicit "show me" / "search now"

Return ONLY a valid JSON object. No explanation, no markdown.

Keys:
  "action"           : string (one of: "chat", "compare", "ask_questions", "search_products")
  "reason"           : string (brief reasoning)
  "followUpText"     : string (only for "ask_questions" or "chat")
  "searchQuery"      : string (only for "search_products")
  "comparisonTarget" : object (only for "compare")

Conversation History:
${historyText || "None"}

User's New Message: "${query}"

Return ONLY the JSON object.`;

  try {
    const raw = await generate(prompt);
    return parseJSON(raw);
  } catch (error) {
    console.error("[GroqService] Context analysis failed:", error.message);
    return { action: "search_products", reason: "Fallback to search on error.", searchQuery: query };
  }
}

async function generateShoppingGuideStream(query, requirements, products, streamCallback) {
  const pListText = products.map((p, idx) =>
    `${idx + 1}. Name: ${p.name} | Price: ₹${p.price.toLocaleString("en-IN")} | Brand: ${p.brand} | Rating: ${p.rating}/5 (${p.reviews} reviews) | Camera: ${p.camera} | Battery: ${p.battery}`
  ).join("\n");

  const prompt = `You are a premium AI Shopping Assistant.
Analyze the user's requirement and the fetched Amazon products below to write an intelligent, helpful product guide.

Requirements:
Category: ${requirements.category}
Budget: ₹${requirements.budget || "No limit"}
Brand: ${requirements.brand || "Any"}
Features: ${(requirements.features || []).join(", ") || "Any"}
User's query: "${query}"

Fetched Products:
${pListText}

Write a structured recommendation in friendly Markdown:
1. Brief opening explaining you analyzed the options.
2. Select a Top Pick — explain why, list Pros and Cons, and Best Use Case.
3. Mention a Budget Option and a Premium Option.
4. Any Better Alternatives from the pool.
5. Polite closing asking if the user wants to compare or read reviews.

Use full product names, not index numbers.

Response:`;

  await generateStream(prompt, streamCallback);
}

async function generateShoppingGuide(query, requirements, products) {
  let guideText = "";
  await generateShoppingGuideStream(query, requirements, products, chunk => { guideText += chunk; });
  return guideText;
}

module.exports = {
  isSmalltalk,
  getChatResponse,
  generalChat,
  extractRequirements,
  generateProsCons,
  generateComparison,
  summariseReviews,
  generateMockReviews,
  analyzeIntentAndContext,
  generateShoppingGuideStream,
  generateShoppingGuide,
};
