const nodemailer = require("nodemailer");

const EMAIL_ADDRESS = process.env.EMAIL_ADDRESS || "";
const EMAIL_PASSWORD = process.env.EMAIL_PASSWORD || "";
const FRONTEND_URL = process.env.FRONTEND_URL || "http://localhost:5173";

async function sendPasswordResetEmail(toEmail, resetToken) {
  const resetLink = `${FRONTEND_URL}/reset-password?token=${resetToken}`;
  
  if (!EMAIL_ADDRESS || !EMAIL_PASSWORD) {
    console.warn("[EmailService] EMAIL_ADDRESS or EMAIL_PASSWORD not set. Skipping email send.");
    console.log(`\n======================================================`);
    console.log(`[EmailService] DEVELOPMENT MODE - Reset password link:`);
    console.log(`  ${resetLink}`);
    console.log(`======================================================\n`);
    return;
  }

  const transporter = nodemailer.createTransport({
    service: "gmail",
    auth: {
      user: EMAIL_ADDRESS,
      pass: EMAIL_PASSWORD
    }
  });

  const mailOptions = {
    from: `"Shopping AI" <${EMAIL_ADDRESS}>`,
    to: toEmail,
    subject: "Reset your Shopping AI password",
    text: `SHOPPING AI — Reset your password\n\nWe received a request to reset the password for your account.\n\nReset link (expires in 15 minutes):\n${resetLink}\n\nIf you did not request a password reset, ignore this email.\n\n— Shopping AI`,
    html: `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1.0">
        <title>Reset your password</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0F172A; margin: 0; padding: 0; }
          .wrapper { max-width: 560px; margin: 40px auto; }
          .card { background: #1E293B; border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 40px 36px; }
          .logo { font-size: 13px; font-weight: 900; letter-spacing: 0.1em; color: #6366F1; margin-bottom: 28px; }
          h1 { font-size: 22px; font-weight: 700; color: #E2E8F0; margin: 0 0 12px; }
          p  { font-size: 15px; color: #94A3B8; line-height: 1.6; margin: 0 0 24px; }
          .btn { display: inline-block; padding: 14px 32px; background: linear-gradient(135deg,#6366F1,#8B5CF6); color: #fff; text-decoration: none; border-radius: 8px; font-size: 15px; font-weight: 600; letter-spacing: 0.02em; }
          .link-note { font-size: 13px; color: #475569; margin-top: 28px; }
          .link-note a { color: #6366F1; word-break: break-all; }
          .expire { font-size: 13px; color: #F87171; margin-top: 20px; }
          .footer { font-size: 12px; color: #334155; text-align: center; margin-top: 32px; }
        </style>
      </head>
      <body>
        <div class="wrapper">
          <div class="card">
            <div class="logo">SHOPPING AI</div>
            <h1>Reset your password</h1>
            <p>We received a request to reset the password for your account. Click the button below to choose a new password.</p>
            <a href="${resetLink}" class="btn">Reset Password</a>
            <p class="expire">This link expires in 15 minutes.</p>
            <p class="link-note">
              Button not working? Paste this link into your browser:<br>
              <a href="${resetLink}">${resetLink}</a>
            </p>
            <p style="margin-top:24px;font-size:13px;color:#475569;">
              If you did not request a password reset, you can safely ignore this email. Your password will not change.
            </p>
          </div>
          <div class="footer">Kavya S &copy; 2026 &middot; Shopping AI</div>
        </div>
      </body>
      </html>
    `.trim()
  };

  try {
    const info = await transporter.sendMail(mailOptions);
    console.log(`[EmailService] Password reset email sent: ${info.messageId} to ${toEmail}`);
  } catch (error) {
    console.error(`[EmailService] Failed to send email: ${error.message}`);
    throw new Error(`Failed to send password reset email: ${error.message}`);
  }
}

module.exports = { sendPasswordResetEmail };
