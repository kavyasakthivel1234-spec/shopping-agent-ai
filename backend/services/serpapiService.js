const fs = require("fs");
const path = require("path");
const CachedProduct = require("../models/CachedProduct");

const SERP_API_KEY = (process.env.SERP_API_KEY || "").trim();
const PRODUCTS_JSON_PATH = path.join(__dirname, "../products.json");

const CATEGORY_ALIASES = {
  "phone": "smartphone",
  "mobile": "smartphone",
  "smartphone": "smartphone",
  "android": "smartphone",
  "iphone": "smartphone",
  "watch": "smartwatch",
  "smartwatch": "smartwatch",
  "wearable": "smartwatch",
  "earbuds": "headphones",
  "earphone": "headphones",
  "headphone": "headphones",
  "headset": "headphones",
  "earbud": "headphones",
  "laptop": "laptop",
  "notebook": "laptop",
  "tab": "tablet",
  "tablet": "tablet",
  "ipad": "tablet",
};

const FALLBACK_CATALOGUE = [
  {"id":"amz-sp-001","source":"Amazon","source_type":"Local","data_mode":"mock","name":"Samsung Galaxy S23 FE","brand":"Samsung","price":34999,"category":"smartphone","rating":4.4,"reviews":2341,"camera":"50MP triple camera","battery":"4500mAh","thumbnail":"","link":"https://www.amazon.in/s?k=Samsung+Galaxy+S23+FE"},
  {"id":"amz-sp-002","source":"Amazon","source_type":"Local","data_mode":"mock","name":"OnePlus 12R","brand":"OnePlus","price":39999,"category":"smartphone","rating":4.5,"reviews":5123,"camera":"50MP good camera","battery":"5500mAh","thumbnail":"","link":"https://www.amazon.in/s?k=OnePlus+12R"},
  {"id":"amz-sp-003","source":"Amazon","source_type":"Local","data_mode":"mock","name":"Redmi Note 13 5G","brand":"Xiaomi","price":18999,"category":"smartphone","rating":4.3,"reviews":8902,"camera":"108MP good camera","battery":"5000mAh","thumbnail":"","link":"https://www.amazon.in/s?k=Redmi+Note+13+5G"},
  {"id":"amz-sp-004","source":"Amazon","source_type":"Local","data_mode":"mock","name":"iQOO Z9 Lite 5G","brand":"iQOO","price":12999,"category":"smartphone","rating":4.2,"reviews":3210,"camera":"50MP good camera","battery":"5000mAh","thumbnail":"","link":"https://www.amazon.in/s?k=iQOO+Z9+Lite+5G"},
  {"id":"amz-sp-005","source":"Amazon","source_type":"Local","data_mode":"mock","name":"Motorola Edge 50 Fusion","brand":"Motorola","price":22999,"category":"smartphone","rating":4.3,"reviews":4567,"camera":"50MP OIS camera","battery":"5000mAh","thumbnail":"","link":"https://www.amazon.in/s?k=Motorola+Edge+50+Fusion"},
  {"id":"amz-lp-001","source":"Amazon","source_type":"Local","data_mode":"mock","name":"HP Pavilion 15","brand":"HP","price":54999,"category":"laptop","rating":4.2,"reviews":1234,"camera":"720p webcam","battery":"41Whr","thumbnail":"","link":"https://www.amazon.in/s?k=HP+Pavilion+15"},
  {"id":"amz-lp-002","source":"Amazon","source_type":"Local","data_mode":"mock","name":"Lenovo IdeaPad Slim 3","brand":"Lenovo","price":44999,"category":"laptop","rating":4.1,"reviews":2109,"camera":"720p webcam","battery":"45Whr","thumbnail":"","link":"https://www.amazon.in/s?k=Lenovo+IdeaPad+Slim+3"},
  {"id":"amz-lp-003","source":"Amazon","source_type":"Local","data_mode":"mock","name":"ASUS VivoBook 15","brand":"ASUS","price":49999,"category":"laptop","rating":4.3,"reviews":3456,"camera":"720p webcam","battery":"42Whr","thumbnail":"","link":"https://www.amazon.in/s?k=ASUS+VivoBook+15"},
  {"id":"amz-lp-004","source":"Amazon","source_type":"Local","data_mode":"mock","name":"HP Victus 15","brand":"HP","price":62999,"category":"laptop","rating":4.4,"reviews":5678,"camera":"720p webcam","battery":"52Whr","thumbnail":"","link":"https://www.amazon.in/s?k=HP+Victus+15"},
  {"id":"amz-hp-001","source":"Amazon","source_type":"Local","data_mode":"mock","name":"Sony WH-CH720N","brand":"Sony","price":5999,"category":"headphones","rating":4.4,"reviews":7890,"camera":"N/A","battery":"35 hours playback","thumbnail":"","link":"https://www.amazon.in/s?k=Sony+WH-CH720N"},
  {"id":"amz-hp-002","source":"Amazon","source_type":"Local","data_mode":"mock","name":"JBL Tune 760NC","brand":"JBL","price":4499,"category":"headphones","rating":4.3,"reviews":6543,"camera":"N/A","battery":"35 hours playback","thumbnail":"","link":"https://www.amazon.in/s?k=JBL+Tune+760NC"},
  {"id":"amz-sw-001","source":"Amazon","source_type":"Local","data_mode":"mock","name":"Samsung Galaxy Watch 6","brand":"Samsung","price":24999,"category":"smartwatch","rating":4.4,"reviews":3210,"camera":"N/A","battery":"40 hours battery","thumbnail":"","link":"https://www.amazon.in/s?k=Samsung+Galaxy+Watch+6"},
  {"id":"amz-sw-002","source":"Amazon","source_type":"Local","data_mode":"mock","name":"Amazfit GTR 4","brand":"Amazfit","price":12999,"category":"smartwatch","rating":4.3,"reviews":4567,"camera":"N/A","battery":"14-day battery","thumbnail":"","link":"https://www.amazon.in/s?k=Amazfit+GTR+4"},
  {"id":"amz-tb-001","source":"Amazon","source_type":"Local","data_mode":"mock","name":"Samsung Galaxy Tab A9","brand":"Samsung","price":18999,"category":"tablet","rating":4.2,"reviews":2345,"camera":"8MP camera","battery":"7040mAh","thumbnail":"","link":"https://www.amazon.in/s?k=Samsung+Galaxy+Tab+A9"},
];

if (SERP_API_KEY) {
  console.log("======================================================");
  console.log("[AmazonService] SERP_API_KEY found: YES");
  console.log("[AmazonService] Real Amazon mode enabled");
  console.log(`[AmazonService] Using Amazon India (amazon.in)`);
  console.log(`[AmazonService] Key preview: ${SERP_API_KEY.substring(0, 8)}...${SERP_API_KEY.substring(SERP_API_KEY.length - 4)}`);
  console.log("======================================================");
} else {
  console.log("======================================================");
  console.log("[AmazonService] SERP_API_KEY found: NO");
  console.log("[AmazonService] Mock product mode enabled");
  console.log("[AmazonService] Add SERP_API_KEY to .env to enable real Amazon search");
  console.log("======================================================");
}

// Helper to parse price
function parsePrice(raw) {
  if (typeof raw === "number") return raw;
  if (!raw) return 0;
  const cleaned = String(raw).replace(/[^\d.]/g, "");
  return parseFloat(cleaned) || 0;
}

// Helper to parse float
function parseFloatSafe(raw) {
  try {
    return parseFloat(raw) || 0;
  } catch {
    return 0;
  }
}

// Helper to parse int
function parseIntSafe(raw) {
  if (typeof raw === "number") return Math.floor(raw);
  if (!raw) return 0;
  const cleaned = String(raw).replace(/[^\d]/g, "");
  return parseInt(cleaned, 10) || 0;
}

// Extract spec from product item (e.g. camera, battery)
function extractSpec(item, keywords) {
  const fields = ["extensions", "snippet", "title", "description", "highlights"];
  for (const field of fields) {
    let value = item[field] || "";
    if (Array.isArray(value)) {
      value = value.join(" ");
    }
    value = String(value);
    for (const kw of keywords) {
      const regex = new RegExp(`(\\d[\\d,]*[\\s]*${kw}[a-z\\s]*)`, "i");
      const match = value.match(regex);
      if (match) {
        return match[0].trim().replace(/\b\w/g, c => c.toUpperCase());
      }
    }
  }
  return "N/A";
}

async function searchAmazon(requirements) {
  const originalQuery = requirements.original_query || requirements.category || "";
  const category = (requirements.category || "").toLowerCase().trim();
  const budget = parseFloat(requirements.budget || 0);
  const features = requirements.features || [];

  console.log(`\n[AmazonService] User Query: ${originalQuery || category || "unknown"}`);

  if (SERP_API_KEY) {
    try {
      // Build search query by stripping budget phrases
      let query = originalQuery;
      if (query) {
        query = query.replace(/\b(under|below|within|upto|up\s+to)\s*[₹rs.]*\s*[\d,]+\s*k?\b/gi, "").trim();
        query = query.replace(/[₹rs.]+\s*[\d,]+\s*k?\b/gi, "").trim();
      } else {
        const parts = category ? [category] : [];
        parts.push(...features.slice(0, 2));
        query = parts.join(" ").trim() || "products";
      }

      console.log(`[AmazonService] Searching Amazon India via SerpAPI: "${query}"`);
      const url = `https://serpapi.com/search.json?engine=amazon&amazon_domain=amazon.in&k=${encodeURIComponent(query)}&api_key=${SERP_API_KEY}`;
      
      const response = await fetch(url, { headers: { "User-Agent": "ShoppingAssistant/4.0" } });
      if (!response.ok) {
        throw new Error(`SerpAPI error: ${response.status} ${response.statusText}`);
      }

      const raw = await response.json();
      const results = raw.shopping_results || raw.organic_results || [];

      if (results.length > 0) {
        console.log(`[AmazonService] Product Source: AMAZON_SERPAPI`);
        console.log(`[AmazonService] Successfully fetched ${results.length} real Amazon products`);
        
        const products = [];
        const ts = Date.now();

        for (let i = 0; i < Math.min(20, results.length); i++) {
          const item = results[i];
          const price = parsePrice(item.price || item.extracted_price || 0);

          // Apply budget filter
          if (budget > 0 && price > 0 && price > budget) {
            continue;
          }

          const rating = parseFloatSafe(item.rating || 0);
          const reviews = parseIntSafe(item.reviews || item.ratings_total || 0);
          
          let avail = true;
          if (item.in_stock !== undefined) {
            avail = typeof item.in_stock === "string" ? !item.in_stock.toLowerCase().includes("out") : Boolean(item.in_stock);
          }

          const pObj = {
            id: `amz-real-${i.toString().padStart(4, "0")}-${ts}`,
            name: item.title || "Unknown Product",
            price: price,
            brand: item.brand || "",
            rating: rating,
            reviews: reviews,
            camera: extractSpec(item, ["camera", "mp"]),
            battery: extractSpec(item, ["battery", "mah", "hour"]),
            thumbnail: item.thumbnail || "",
            link: item.link || "",
            source: "Amazon",
            source_type: "Real",
            data_mode: "amazon",
            availability: avail
          };

          products.push(pObj);

          // Cache product in MongoDB asynchronously so details (pros/cons, reviews) can be retrieved by ID
          CachedProduct.create(pObj).catch(err => {
            // Silently ignore duplicates
            if (err.code !== 11000) {
              console.error("[CachedProduct] Error caching:", err.message);
            }
          });
        }

        console.log(`[AmazonService] First ${Math.min(3, products.length)} products:`);
        for (let i = 0; i < Math.min(3, products.length); i++) {
          const p = products[i];
          console.log(`  ${i + 1}. ${p.name} | ₹${p.price.toLocaleString("en-IN")} | ${p.brand}`);
        }
        console.log("");

        return products;
      }

      console.warn("[AmazonService] SerpAPI returned 0 results. Falling back to mock data.");
    } catch (error) {
      console.error(`[AmazonService] SerpAPI search failed: ${error.message}. Falling back to mock data.`);
    }
  }

  // Fallback to local catalogue
  console.log(`[AmazonService] Product Source: LOCAL_MOCK`);
  const localProducts = loadLocalCatalogue(requirements);
  console.log(`[AmazonService] Serving ${localProducts.length} mock products\n`);
  return localProducts;
}

function loadLocalCatalogue(requirements) {
  const rawCategory = (requirements.category || "").toLowerCase().trim();
  const budget = parseFloat(requirements.budget || 0);
  const targetCategory = CATEGORY_ALIASES[rawCategory] || rawCategory;

  let localDb = [];
  try {
    if (fs.existsSync(PRODUCTS_JSON_PATH)) {
      const fileData = fs.readFileSync(PRODUCTS_JSON_PATH, "utf-8");
      localDb = JSON.parse(fileData);
    }
  } catch (err) {
    console.error("[AmazonService] Error reading products.json:", err.message);
  }

  // Merge static lists
  const pool = [...FALLBACK_CATALOGUE, ...localDb];
  const seen = new Set();
  const filtered = [];

  for (const p of pool) {
    // Normalise category
    const pCat = (p.category || "").toLowerCase();
    const pcResolved = CATEGORY_ALIASES[pCat] || pCat;
    const catResolved = CATEGORY_ALIASES[targetCategory] || targetCategory;

    // Filter by category (for local catalog)
    if (targetCategory && !pcResolved.includes(catResolved) && !catResolved.includes(pcResolved)) {
      continue;
    }

    // Filter by budget
    if (budget > 0 && p.price > budget) {
      continue;
    }

    const key = `${p.name.toLowerCase()}_${p.price}`;
    if (!seen.has(key)) {
      seen.add(key);
      filtered.push({
        id: p.id,
        name: p.name,
        price: p.price,
        brand: p.brand || "",
        category: p.category || rawCategory,
        rating: p.rating || 0.0,
        reviews: p.reviews || 0,
        camera: p.camera || "N/A",
        battery: p.battery || "N/A",
        thumbnail: p.thumbnail || "",
        link: p.link || "",
        source: p.source || "Local",
        source_type: p.source_type || "Local",
        data_mode: p.data_mode || "mock",
        availability: p.availability !== undefined ? p.availability : true
      });
    }
  }

  return filtered;
}

// Function to find a product by ID (checking static pool, mock file, and MongoDB cache)
async function findProductById(productId) {
  // 1. Check static fallback catalogue
  let product = FALLBACK_CATALOGUE.find(p => p.id === productId);
  if (product) return { ...product };

  // 2. Check local products.json file
  try {
    if (fs.existsSync(PRODUCTS_JSON_PATH)) {
      const localDb = JSON.parse(fs.readFileSync(PRODUCTS_JSON_PATH, "utf-8"));
      product = localDb.find(p => p.id === productId);
      if (product) return { ...product };
    }
  } catch (err) {
    console.error("[AmazonService] Error reading products.json:", err.message);
  }

  // 3. Check MongoDB cache (covers real products)
  const cached = await CachedProduct.findOne({ id: productId });
  if (cached) {
    return cached.toObject();
  }

  throw new Error(`Product with ID '${productId}' not found.`);
}

module.exports = {
  searchAmazon,
  findProductById,
  CATEGORY_ALIASES
};
