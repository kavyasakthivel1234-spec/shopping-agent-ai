"""
groq_service.py
---------------
AI / NLP layer — Groq (Llama 3.3 70B).

Single responsibility: understand user intent and extract structured filters.
Does NOT search products, does NOT generate recommendations.

The class is still named GeminiService so all existing imports keep working.

Extracted filter schema (full):
    {
        "product":    str,          # e.g. "mobile", "laptop", "chocolate snacks"
        "brand":      str | null,   # e.g. "Samsung", null
        "maxPrice":   float | null, # e.g. 20000.0, null
        "minPrice":   float | null,
        "minRating":  float | null, # e.g. 4.0, null
        "color":      str | null,
        "size":       str | null,
        "storage":    str | null,
        "ram":        str | null,
        "flavor":     str | null,
        "material":   str | null,
        "features":   list[str],    # extra specs, e.g. ["5G", "fast charging"]
        "searchQuery": str          # ready-to-use Amazon search string
    }
"""

import json
import logging
import os
import re

from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Small-talk detector
# ---------------------------------------------------------------------------
_SMALLTALK = re.compile(
    r"^\s*(hi+|hello+|hey+|howdy|greetings|sup|what'?s up|how are you|"
    r"how r u|good morning|good afternoon|good evening|"
    r"who are you|what can you do|help me|what do you do)\s*[!?.]*\s*$",
    re.IGNORECASE,
)


class GeminiService:
    """
    Groq-backed NLP service.
    Retains the name GeminiService for import compatibility.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not self.api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is missing. Get a free key at https://console.groq.com/keys"
            )
        self.client     = Groq(api_key=self.api_key)
        self.model_name = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
        print(f"[GroqService] Model: {self.model_name}")

    # ------------------------------------------------------------------ core
    def _generate(self, prompt: str, temperature: float = 0.3) -> str:
        try:
            res = self.client.chat.completions.create(
                model       = self.model_name,
                messages    = [{"role": "user", "content": prompt}],
                temperature = temperature,
                max_tokens  = 1024,
            )
            return res.choices[0].message.content.strip()
        except Exception as exc:
            err = str(exc)
            logger.error("[GroqService] API error: %s", err)
            if "rate_limit" in err.lower() or "429" in err:
                raise RuntimeError("Groq rate limit reached. Please wait and retry.") from exc
            if "401" in err or "403" in err or "api_key" in err.lower():
                raise RuntimeError("Groq API key invalid. Check GROQ_API_KEY in .env.") from exc
            raise RuntimeError(f"Groq call failed: {exc}") from exc

    def _parse_json(self, raw: str) -> dict:
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if m:
            cleaned = m.group(0)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Groq returned invalid JSON.\nRaw: {raw}\nError: {exc}") from exc

    # ------------------------------------------------------------------ smalltalk
    @staticmethod
    def is_smalltalk(query: str) -> bool:
        return bool(_SMALLTALK.match(query.strip()))

    def chat_response(self, message: str) -> str:
        prompt = (
            "You are a friendly AI shopping assistant. "
            "Reply warmly and briefly (max 3 sentences, no markdown). "
            "Mention you can help find any product on Amazon India.\n\n"
            f"User: {message}"
        )
        try:
            return self._generate(prompt, temperature=0.7)
        except RuntimeError:
            return (
                "Hello! I'm your AI Shopping Assistant. "
                "I can help you find any product on Amazon India. "
                "What are you looking for today?"
            )

    def chat(self, query: str) -> str:
        try:
            return self._generate(
                f"You are a friendly AI assistant. Answer naturally, no markdown.\nUser: {query}",
                temperature=0.7,
            )
        except RuntimeError as exc:
            return f"I'm having trouble connecting right now. ({exc})"

    # ------------------------------------------------------------------ main NLP
    def extract_requirements(self, query: str) -> dict:
        """
        Use Groq to extract ALL shopping filters from any natural-language query.

        Returns a rich dict with product, brand, price range, rating,
        color, size, storage, RAM, flavor, material, extra features,
        and a ready-made Amazon search query string.
        """
        prompt = f"""You are a shopping intent extractor for an Amazon India product search engine.

Extract ALL shopping requirements from the user query below.
Return ONLY a valid JSON object — no explanation, no markdown, no code fences.

JSON keys (use null for anything not mentioned):
  "product"    : string  — exact product name/type (e.g. "mobile", "laptop", "chocolate", "dress")
  "brand"      : string | null  — brand name exactly as user said (e.g. "Samsung", "Nike", "Cadbury")
  "maxPrice"   : number | null  — maximum price in INR
  "minPrice"   : number | null  — minimum price in INR
  "minRating"  : number | null  — minimum star rating (e.g. 4, 4.5)
  "color"      : string | null  — color preference (e.g. "blue", "black")
  "size"       : string | null  — size (e.g. "XL", "15 inch", "1kg")
  "storage"    : string | null  — storage (e.g. "128GB", "256GB")
  "ram"        : string | null  — RAM (e.g. "8GB", "16GB")
  "flavor"     : string | null  — flavor (e.g. "chocolate", "vanilla")
  "material"   : string | null  — material (e.g. "cotton", "leather")
  "features"   : array<string>  — extra specs not covered above (e.g. ["5G", "fast charging", "wireless"])

Rules:
- Never invent values the user did not mention.
- "product" must reflect the user's actual intent. If they say "phone" write "phone", "dress" write "dress".
- Prices like "under 20000", "below 500", "max 1500" go into maxPrice.
- Prices like "above 1000", "minimum 500" go into minPrice.
- "4+ stars", "at least 4 stars", "4 star" → minRating: 4.

User query: "{query}"

Return ONLY the JSON object."""

        try:
            raw    = self._generate(prompt, temperature=0.2)
            data   = self._parse_json(raw)
            result = self._normalise_filters(data, query)
            print(f"[GroqService] Extracted filters: {result}")
            logger.info("[GroqService] Filters: %s", result)
            return result
        except Exception as exc:
            logger.warning("[GroqService] LLM extraction failed (%s) — rule-based fallback", exc)
            return self._rule_extract(query)

    def _normalise_filters(self, data: dict, original_query: str) -> dict:
        def _float_or_none(v) -> float | None:
            try:
                return float(v) if v is not None else None
            except (TypeError, ValueError):
                return None

        def _str_or_none(v) -> str | None:
            s = str(v).strip() if v is not None else None
            return s if s and s.lower() not in ("null", "none", "") else None

        product   = _str_or_none(data.get("product")) or original_query.strip()
        brand     = _str_or_none(data.get("brand"))
        max_price = _float_or_none(data.get("maxPrice"))
        min_price = _float_or_none(data.get("minPrice"))
        min_rating = _float_or_none(data.get("minRating"))
        color     = _str_or_none(data.get("color"))
        size      = _str_or_none(data.get("size"))
        storage   = _str_or_none(data.get("storage"))
        ram       = _str_or_none(data.get("ram"))
        flavor    = _str_or_none(data.get("flavor"))
        material  = _str_or_none(data.get("material"))
        features  = [str(f).strip() for f in (data.get("features") or []) if f]

        # Build the Amazon search query
        parts = []
        if brand:    parts.append(brand)
        if color:    parts.append(color)
        if size:     parts.append(size)
        if ram:      parts.append(ram)
        if storage:  parts.append(storage)
        if flavor:   parts.append(flavor)
        if material: parts.append(material)
        parts.append(product)
        if max_price:
            parts.append(f"under {int(max_price)} rupees")
        parts.append("Amazon India")
        search_query = " ".join(parts).strip()

        # Also keep legacy fields so downstream services don't break
        return {
            # Rich filters (new)
            "product":     product,
            "brand":       brand,
            "maxPrice":    max_price,
            "minPrice":    min_price,
            "minRating":   min_rating,
            "color":       color,
            "size":        size,
            "storage":     storage,
            "ram":         ram,
            "flavor":      flavor,
            "material":    material,
            "features":    features,
            "searchQuery": search_query,
            # Legacy fields (kept so orchestrator / recommendation service keep working)
            "category":       product,
            "budget":         max_price or 0.0,
            "original_query": search_query,
        }

    def _rule_extract(self, query: str) -> dict:
        """Fast deterministic fallback when Groq is unavailable."""
        q     = query.strip()
        ql    = q.lower()

        # Budget
        max_price: float | None = None
        m = re.search(r"(?:under|below|upto|up to|within|less than|max|<)\s*[₹rs.]*\s*([\d,]+)\s*k?\b", ql, re.I)
        if m:
            val = float(m.group(1).replace(",", ""))
            if "k" in m.group(0).lower()[-2:]:
                val *= 1000
            max_price = val

        # Min price
        min_price: float | None = None
        m2 = re.search(r"(?:above|over|min|minimum|at least)\s*[₹rs.]*\s*([\d,]+)\s*k?\b", ql, re.I)
        if m2:
            val2 = float(m2.group(1).replace(",", ""))
            if "k" in m2.group(0).lower()[-2:]:
                val2 *= 1000
            min_price = val2

        # Rating
        min_rating: float | None = None
        mr = re.search(r"(\d+\.?\d*)\+?\s*star", ql, re.I)
        if mr:
            min_rating = float(mr.group(1))

        product     = q
        search_query = f"{q} Amazon India"

        return {
            "product":        product,
            "brand":          None,
            "maxPrice":       max_price,
            "minPrice":       min_price,
            "minRating":      min_rating,
            "color":          None,
            "size":           None,
            "storage":        None,
            "ram":            None,
            "flavor":         None,
            "material":       None,
            "features":       [],
            "searchQuery":    search_query,
            "category":       product,
            "budget":         max_price or 0.0,
            "original_query": search_query,
        }

    # ------------------------------------------------------------------ downstream AI methods
    def generate_pros_cons(self, product: dict) -> dict:
        prompt = f"""Product expert analysis. Return ONLY valid JSON, no markdown.
Keys: "pros": array of 2-4 strings, "cons": array of 2-4 strings.
Product: {product.get("name")} | ₹{product.get("price", 0):,.0f} | {product.get("brand", "")}
Return ONLY the JSON."""
        try:
            data = self._parse_json(self._generate(prompt))
            return {
                "pros": [str(p).strip() for p in (data.get("pros") or [])],
                "cons": [str(c).strip() for c in (data.get("cons") or [])],
            }
        except Exception:
            return {"pros": [], "cons": []}

    def generate_comparison(self, p1: dict, p2: dict) -> dict:
        prompt = f"""Compare two products. Return ONLY valid JSON, no markdown.
Keys: "camera":{{}}, "battery":{{}}, "price":{{}}, "winner":string, "summary":string.
Each of camera/battery/price has "product1" and "product2" string values.
P1: {p1.get("name")} ₹{p1.get("price",0):,.0f}
P2: {p2.get("name")} ₹{p2.get("price",0):,.0f}
Return ONLY the JSON."""
        try:
            data = self._parse_json(self._generate(prompt))
            return {
                "camera":  data.get("camera",  {}),
                "battery": data.get("battery", {}),
                "price":   data.get("price",   {}),
                "winner":  str(data.get("winner",  "")),
                "summary": str(data.get("summary", "")),
            }
        except Exception:
            return {"camera": {}, "battery": {}, "price": {}, "winner": "", "summary": ""}

    def summarise_reviews(self, reviews: list[str]) -> dict:
        text   = "\n".join(f"- {r}" for r in reviews)
        prompt = f"""Review analyst. Return ONLY valid JSON, no markdown.
Keys: "liked": array of short strings, "disliked": array of short strings.
Reviews:\n{text}\nReturn ONLY the JSON."""
        try:
            data = self._parse_json(self._generate(prompt))
            return {
                "liked":    [str(t).strip() for t in (data.get("liked")    or [])],
                "disliked": [str(t).strip() for t in (data.get("disliked") or [])],
            }
        except Exception:
            return {"liked": [], "disliked": []}
