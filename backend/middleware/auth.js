const jwt = require("jsonwebtoken");
const User = require("../models/User");

const JWT_SECRET = process.env.JWT_SECRET || process.env.JWT_SECRET_KEY || "change_this_to_a_secure_secret";

const protect = async (req, res, next) => {
  let token;

  // Debug logging
  console.log("Authorization header received in backend:");
  console.log(req.headers.authorization);

  if (
    req.headers.authorization &&
    req.headers.authorization.startsWith("Bearer ")
  ) {
    token = req.headers.authorization.split(" ")[1];
  }

  if (!token || token === "null" || token === "undefined") {
    console.log("[AuthMiddleware] No valid token found.");
    return res.status(401).json({
      message: "Not authenticated"
    });
  }

  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    
    // Debug logging
    console.log("Decoded token payload:");
    console.log(decoded);

    // Extract the user ID from decoded.id (or decoded.userId fallback)
    const userId = decoded.id || decoded.userId || decoded.sub;
    
    const user = await User.findById(userId);
    if (!user) {
      console.log(`[AuthMiddleware] User not found in database for ID: ${userId}`);
      return res.status(401).json({
        message: "Not authenticated"
      });
    }

    // Attach user to request
    req.user = user;
    req.user.id = user._id.toString();

    next();
  } catch (error) {
    console.error("JWT Error:", error);
    return res.status(401).json({
      message: "Invalid token"
    });
  }
};

module.exports = protect;
