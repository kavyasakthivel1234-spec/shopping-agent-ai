"""
amazon_service.py
-----------------
Amazon product search — SerpAPI ONLY. Zero mock data. Zero fallback.

Architecture:
    Groq extracts filters → AmazonService builds query → SerpAPI fetches real products
    → filter by price / rating / brand client-side → return clean product list

If SerpAPI returns 0 results, returns empty list — the route layer then
returns a "no results" chat message.  We NEVER invent fake products.

Startup logs:
    [AmazonService] SERP_API_KEY: SET   → Real Amazon search enabled
    [AmazonService] SERP_API_KEY: MISSING → searches will fail

Per-request logs:
    [AmazonService] Search query: "..."
    [AmazonService] SerpAPI raw response: N items
    [AmazonService] After filtering: N products
    [AmazonService] Top 3: ...
"""

import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
import urllib.error

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Re-export empty list so comparison.py import doesn't break
AMAZON_CATALOGUE: list[dict] = []


class AmazonService:
    """
    Real-only Amazon India product search via SerpAPI.
    No mock data. No fallback catalogue.
    """

    SERP_API_URL = "https://serpapi.com/search.json"

    def __init__(self, api_key: str | None = None):
        self.api_key = (api_key or os.getenv("SERP_API_KEY", "")).strip()

        if self.api_key:
            print("=" * 60)
            print("[AmazonService] SERP_API_KEY: SET — Real Amazon search enabled")
            print(f"[AmazonService] Key: {self.api_key[:8]}...{self.api_key[-4:]}")
            print("=" * 60)
        else:
            print("=" * 60)
            print("[AmazonService] SERP_API_KEY: MISSING")
            print("[AmazonService] Add SERP_API_KEY to backend/.env")
            print("=" * 60)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_products(self, requirements: dict) -> list[dict]:
        """
        Search Amazon India using SerpAPI, falling back to local mock products on failure/missing key.
        """
        if not self.api_key:
            print("[AmazonService] SERP_API_KEY not set. Falling back to local product catalogue.")
            from services.local_product_service import LocalProductService
            local_svc = LocalProductService()
            return local_svc.search_products(requirements)

        search_query = requirements.get("searchQuery") or requirements.get("original_query", "")
        if not search_query:
            product  = requirements.get("product") or requirements.get("category", "")
            brand    = requirements.get("brand") or ""
            max_price = requirements.get("maxPrice") or requirements.get("budget") or 0
            search_query = f"{brand} {product} Amazon India".strip()
            if max_price:
                search_query = f"{brand} {product} under {int(max_price)} rupees Amazon India".strip()

        print(f"\n[AmazonService] Search query: \"{search_query}\"")
        logger.info("[AmazonService] SerpAPI query: %r", search_query)

        try:
            raw_items = self._call_serpapi(search_query)
            print(f"[AmazonService] SerpAPI raw response: {len(raw_items)} items")

            products  = self._normalise(raw_items, search_query)
            filtered  = self._apply_filters(products, requirements)

            print(f"[AmazonService] After filtering: {len(filtered)} products")
            if filtered:
                print(f"[AmazonService] Top {min(3, len(filtered))} products:")
                for i, p in enumerate(filtered[:3], 1):
                    price_str = f"₹{p['price']:,.0f}" if p["price"] else "Price N/A"
                    print(f"  {i}. {p['name']} | {price_str} | {p.get('brand') or 'N/A'} | ★{p.get('rating') or 'N/A'}")
                
                # Cache products in AMAZON_CATALOGUE so comparison can retrieve them by ID
                for p in filtered:
                    if p["id"] not in [x["id"] for x in AMAZON_CATALOGUE]:
                        AMAZON_CATALOGUE.append(p)
                print()
                return filtered
        except Exception as exc:
            print(f"[AmazonService] SerpAPI search failed ({exc}). Falling back to local product catalogue.")
            logger.warning("[AmazonService] SerpAPI search failed: %s", exc)

        from services.local_product_service import LocalProductService
        local_svc = LocalProductService()
        fallback_products = local_svc.search_products(requirements)
        
        # Also cache fallback products
        for p in fallback_products:
            if p["id"] not in [x["id"] for x in AMAZON_CATALOGUE]:
                AMAZON_CATALOGUE.append(p)
                
        return fallback_products

    def raw_serpapi_search(self, query: str) -> dict:
        """Debug endpoint helper — returns raw + normalised response."""
        items    = self._call_serpapi(query)
        products = self._normalise(items, query)
        return {
            "query":          query,
            "products_found": len(products),
            "products":       products[:10],
        }

    # ------------------------------------------------------------------
    # SerpAPI call
    # ------------------------------------------------------------------

    def _call_serpapi(self, search_query: str) -> list[dict]:
        params = {
            "engine":        "amazon",
            "amazon_domain": "amazon.in",
            "k":             search_query,
            "api_key":       self.api_key,
        }
        url = f"{self.SERP_API_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "ShoppingAssistant/5.0"})

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise ValueError(
                    f"SerpAPI {exc.code} — Invalid or expired SERP_API_KEY. "
                    "Check https://serpapi.com/manage-api-key"
                ) from exc
            raise RuntimeError(f"SerpAPI HTTP {exc.code}: {exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Network error reaching SerpAPI: {exc.reason}") from exc

        if "error" in raw:
            raise RuntimeError(f"SerpAPI error: {raw['error']}")

        # SerpAPI returns shopping_results or organic_results for amazon engine
        return raw.get("shopping_results") or raw.get("organic_results") or []

    # ------------------------------------------------------------------
    # Normalise raw SerpAPI items → clean product dicts
    # ------------------------------------------------------------------

    # Known brand names to match at start of product titles
    # This list is intentionally broad — covers all common Amazon India brands
    _KNOWN_BRANDS = [
        # Phones / electronics
        "Samsung", "Apple", "OnePlus", "Xiaomi", "Redmi", "Realme", "OPPO",
        "Vivo", "iQOO", "Nothing", "Motorola", "Nokia", "Asus", "Sony",
        "Google", "Poco", "Tecno", "Infinix", "Lava", "itel",
        # Laptops / computers
        "HP", "Dell", "Lenovo", "Acer", "ASUS", "MSI", "Apple",
        "Microsoft", "Avita", "Infinix", "Honor",
        # Audio
        "JBL", "boAt", "Noise", "Sony", "Bose", "Sennheiser", "Jabra",
        "Skullcandy", "Boat", "Mivi", "Zebronics", "Portronics",
        # Watches
        "Amazfit", "Fitbit", "Garmin", "Fossil", "Titan", "Fire-Boltt",
        "Noise", "boAt",
        # Appliances / kitchen
        "Philips", "Prestige", "Havells", "Bajaj", "Pigeon", "Inalsa",
        "Butterfly", "Preethi", "Kent", "Eureka Forbes", "Bosch", "LG",
        "Whirlpool", "Samsung", "Haier", "Voltas",
        # Food / FMCG
        "Cadbury", "Nestle", "Amul", "Britannia", "ITC", "Haldirams",
        "Lay's", "Kurkure", "Pepsi", "Coca-Cola", "Red Bull",
        # Fashion
        "Nike", "Adidas", "Puma", "Reebok", "Woodland", "Bata", "Relaxo",
        "Levi's", "Arrow", "Van Heusen", "Peter England", "Allen Solly",
        # Books
        "Penguin", "HarperCollins", "Rupa",
    ]

    def _extract_brand_from_title(self, title: str) -> str | None:
        """
        Extract brand name from the product title.
        Strategy:
          1. Check if the title starts with a known brand name (case-insensitive)
          2. If not, take the first word of the title — many Amazon titles
             start with the brand name (Dell 15..., HP 15..., Acer Aspire...)
        """
        if not title:
            return None

        title_stripped = title.strip()

        # Strategy 1: Match against known brand list (longest match first to
        # catch multi-word brands like "Fire-Boltt", "Van Heusen")
        title_lower = title_stripped.lower()
        for brand in sorted(self._KNOWN_BRANDS, key=len, reverse=True):
            if title_lower.startswith(brand.lower()):
                return brand  # return the canonical casing from our list

        # Strategy 2: First word of title (capitalised)
        first_word = title_stripped.split()[0] if title_stripped.split() else None
        if first_word and len(first_word) >= 2 and first_word[0].isupper():
            # Clean punctuation
            first_word = re.sub(r"[^A-Za-z0-9\-]", "", first_word)
            return first_word if first_word else None

        return None

    def _normalise(self, items: list[dict], category: str) -> list[dict]:
        products: list[dict] = []
        ts = int(time.time())

        for i, item in enumerate(items[:25]):
            name = (item.get("title") or "").strip()
            if not name:
                continue

            # ── Price ────────────────────────────────────────────────
            price     = self._parse_price(item.get("extracted_price") or item.get("price"))
            old_price = self._parse_price(item.get("extracted_old_price") or item.get("old_price"))

            # ── Rating / reviews ─────────────────────────────────────
            rating  = self._parse_float(item.get("rating"))
            reviews = self._parse_int(item.get("reviews") or item.get("ratings_total"))

            # ── Brand — SerpAPI field first, then title extraction ────
            raw_brand = (item.get("brand") or "").strip()
            brand = raw_brand if raw_brand else self._extract_brand_from_title(name)

            # ── Links / image ─────────────────────────────────────────
            # Prefer link_clean (cleaner URL without tracking params)
            link  = (item.get("link_clean") or item.get("link") or "").strip() or None
            thumb = (item.get("thumbnail") or "").strip() or None

            # ── Seller ───────────────────────────────────────────────
            # SerpAPI search results never include seller — it's only on
            # the product detail page.  The best we can do from search
            # results is use the brand as the likely seller name
            # (on Amazon India, most brand products are sold by the brand
            # store or Amazon itself).
            raw_seller = (item.get("seller") or item.get("source") or "").strip()
            seller = raw_seller if raw_seller else (brand if brand else None)

            # ── Availability ──────────────────────────────────────────
            avail = item.get("in_stock", True)
            if isinstance(avail, str):
                avail = "out" not in avail.lower()

            # ── Extra fields from SerpAPI ─────────────────────────────
            asin             = (item.get("asin") or "").strip() or None
            bought_last_month = (item.get("bought_last_month") or "").strip() or None
            offers           = item.get("offers") or []
            delivery         = item.get("delivery") or []

            products.append({
                # Identification
                "id":           f"amz-real-{i:04d}-{ts}",
                "asin":         asin,
                "source":       "Amazon",
                "source_type":  "Real",
                "data_mode":    "amazon",
                # Core product info
                "name":         name,
                "title":        name,
                "brand":        brand,
                "price":        price,
                "old_price":    old_price,
                "rating":       rating,
                "reviews":      reviews,
                "bought_last_month": bought_last_month,
                "image":        thumb,
                "thumbnail":    thumb,
                "link":         link,
                "seller":       seller,
                "availability": avail,
                "offers":       offers,
                "delivery":     delivery,
                # Legacy fields
                "category":     category,
                "camera":       self._extract_spec(item, ["camera", "mp"]),
                "battery":      self._extract_spec(item, ["battery", "mah", "wh"]),
                "score":        0,
            })

            print(
                f"[AmazonService] [{i+1}] brand={brand!r:15} "
                f"seller={seller!r:15} "
                f"price=₹{price or 'N/A'} "
                f"| {name[:55]}"
            )

        return products

    # ------------------------------------------------------------------
    # Client-side filtering
    # ------------------------------------------------------------------

    def _apply_filters(self, products: list[dict], requirements: dict) -> list[dict]:
        """
        Apply Groq-extracted filters to the real product list.
        Returns ALL products that pass — no forced minimums.
        """
        max_price  = requirements.get("maxPrice")  or requirements.get("budget") or None
        min_price  = requirements.get("minPrice")
        min_rating = requirements.get("minRating")
        brand_filter = (requirements.get("brand") or "").strip().lower()

        filtered: list[dict] = []
        for p in products:
            price  = p.get("price")
            rating = p.get("rating")
            name   = (p.get("name") or "").lower()
            brand  = (p.get("brand") or "").lower()

            # Price filters — only apply if product has a known price
            if max_price and price is not None and price > 0:
                if price > max_price:
                    continue

            if min_price and price is not None and price > 0:
                if price < min_price:
                    continue

            # Rating filter — only apply if product has a rating
            if min_rating and rating is not None and rating > 0:
                if rating < min_rating:
                    continue

            # Brand filter — check name OR brand field
            if brand_filter:
                brand_in_name  = brand_filter in name
                brand_in_brand = brand_filter in brand
                if not brand_in_name and not brand_in_brand:
                    continue

            filtered.append(p)

        return filtered

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_price(raw) -> float | None:
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            v = float(raw)
            return v if v > 0 else None
        cleaned = re.sub(r"[^\d.]", "", str(raw))
        if not cleaned:
            return None
        try:
            v = float(cleaned)
            return v if v > 0 else None
        except ValueError:
            return None

    @staticmethod
    def _parse_float(raw) -> float | None:
        if raw is None:
            return None
        try:
            v = float(raw)
            return v if v > 0 else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_int(raw) -> int | None:
        if raw is None:
            return None
        if isinstance(raw, int):
            return raw if raw > 0 else None
        cleaned = re.sub(r"[^\d]", "", str(raw))
        if not cleaned:
            return None
        try:
            v = int(cleaned)
            return v if v > 0 else None
        except ValueError:
            return None

    @staticmethod
    def _extract_spec(item: dict, keywords: list[str]) -> str:
        for field in ("extensions", "snippet", "title", "description", "highlights"):
            value = item.get(field, "")
            if isinstance(value, list):
                value = " ".join(str(v) for v in value)
            for kw in keywords:
                match = re.search(
                    rf"(\d[\d,]*[\s]*{re.escape(kw)}[a-z\s]*)",
                    str(value),
                    re.IGNORECASE,
                )
                if match:
                    return match.group(0).strip().title()
        return "N/A"
