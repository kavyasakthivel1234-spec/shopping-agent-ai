const express = require("express");
const jwt = require("jsonwebtoken");
const User = require("../models/User");
const protect = require("../middleware/auth");
const { sendPasswordResetEmail } = require("../services/emailService");

const router = express.Router();
const JWT_SECRET = process.env.JWT_SECRET || process.env.JWT_SECRET_KEY || "change_this_to_a_secure_secret";

// Helper to generate access token (signs with ID payload)
function generateAccessToken(user) {
  return jwt.sign(
    { id: user._id },
    JWT_SECRET,
    { expiresIn: "7d" }
  );
}

// Helper to generate password reset token (15 mins)
function generateResetToken(email) {
  return jwt.sign(
    { sub: email, purpose: "password_reset" },
    JWT_SECRET,
    { expiresIn: "15m" }
  );
}

// ---------------------------------------------------------------------------
// POST /api/auth/signup
// ---------------------------------------------------------------------------
router.post("/signup", async (req, res) => {
  const { name, email, mobile, password } = req.body;

  if (!name || !email || !mobile || !password) {
    return res.status(400).json({ detail: "All fields (name, email, mobile, password) are required." });
  }

  try {
    const existingEmail = await User.findOne({ email: email.toLowerCase().trim() });
    if (existingEmail) {
      return res.status(409).json({ detail: "An account with this email address already exists." });
    }

    const existingMobile = await User.findOne({ mobile: mobile.trim() });
    if (existingMobile) {
      return res.status(409).json({ detail: "An account with this mobile number already exists." });
    }

    const user = new User({
      name,
      email: email.toLowerCase().trim(),
      mobile: mobile.trim(),
      password
    });

    await user.save();

    res.status(201).json({
      message: "Account created successfully. You can now sign in.",
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        mobile: user.mobile
      }
    });
  } catch (error) {
    console.error("[AuthRoutes] Signup error:", error.message);
    res.status(500).json({ detail: `Internal server error: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// POST /api/auth/login
// ---------------------------------------------------------------------------
router.post("/login", async (req, res) => {
  const { email, mobile, password } = req.body;

  if ((!email && !mobile) || !password) {
    return res.status(400).json({ detail: "Identifier (email or mobile) and password are required." });
  }

  try {
    let query = {};
    if (email) {
      query.email = email.toLowerCase().trim();
    } else {
      query.mobile = mobile.trim();
    }

    const user = await User.findOne(query);
    if (!user) {
      return res.status(401).json({ detail: "Invalid credentials. Account not found." });
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({ detail: "Invalid credentials. Password mismatch." });
    }

    const token = generateAccessToken(user);

    res.json({
      access_token: token,
      token_type: "bearer",
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        mobile: user.mobile
      }
    });
  } catch (error) {
    console.error("[AuthRoutes] Login error:", error.message);
    res.status(500).json({ detail: `Internal server error: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// GET /api/auth/profile (protected)
// ---------------------------------------------------------------------------
router.get("/profile", protect, async (req, res) => {
  res.json({
    id: req.user._id,
    name: req.user.name,
    email: req.user.email,
    mobile: req.user.mobile
  });
});

// ---------------------------------------------------------------------------
// POST /api/auth/forgot-password
// ---------------------------------------------------------------------------
router.post("/forgot-password", async (req, res) => {
  const { email } = req.body;

  if (!email) {
    return res.status(400).json({ detail: "Email is required." });
  }

  const cleanEmail = email.toLowerCase().trim();

  try {
    const user = await User.findOne({ email: cleanEmail });

    if (!user) {
      console.log(`[AuthRoutes] Forgot-password for unknown email: ${cleanEmail}`);
    } else {
      const resetToken = generateResetToken(cleanEmail);
      const expiry = new Date(Date.now() + 15 * 60 * 1000); // 15 mins

      user.reset_token = resetToken;
      user.reset_token_expiry = expiry;
      await user.save();

      await sendPasswordResetEmail(cleanEmail, resetToken).catch(err => {
        console.error("[AuthRoutes] Email trigger failed:", err.message);
      });
    }

    res.json({
      message: "If an account with that email exists, a password reset link has been sent. Please check your inbox (and spam folder)."
    });
  } catch (error) {
    console.error("[AuthRoutes] Forgot-password error:", error.message);
    res.status(500).json({ detail: `Internal server error: ${error.message}` });
  }
});

// ---------------------------------------------------------------------------
// POST /api/auth/reset-password
// ---------------------------------------------------------------------------
router.post("/reset-password", async (req, res) => {
  const { token, password } = req.body;

  if (!token || !password) {
    return res.status(400).json({ detail: "Token and password are required." });
  }

  if (password.length < 6) {
    return res.status(400).json({ detail: "Password must be at least 6 characters." });
  }

  try {
    let decoded;
    try {
      decoded = jwt.verify(token, JWT_SECRET);
    } catch (err) {
      return res.status(400).json({ detail: "Password reset link is invalid or has expired. Please request a new one." });
    }

    if (decoded.purpose !== "password_reset") {
      return res.status(400).json({ detail: "Invalid token purpose." });
    }

    const email = decoded.sub;
    const user = await User.findOne({ email: email });

    if (!user || user.reset_token !== token) {
      return res.status(400).json({ detail: "Password reset link is invalid or has already been used." });
    }

    if (user.reset_token_expiry && new Date() > user.reset_token_expiry) {
      return res.status(400).json({ detail: "Password reset link has expired." });
    }

    user.password = password;
    user.reset_token = null;
    user.reset_token_expiry = null;
    await user.save();

    res.json({ message: "Your password has been reset successfully. You can now sign in." });
  } catch (error) {
    console.error("[AuthRoutes] Reset-password error:", error.message);
    res.status(500).json({ detail: `Internal server error: ${error.message}` });
  }
});

module.exports = router;
