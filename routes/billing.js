import express from "express";
import Stripe from "stripe";

const router = express.Router();

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

/* ===============================
   CREATE CHECKOUT SESSION
=============================== */

router.post("/create-checkout-session", async (req, res) => {

  const { mode } = req.query;

  try {

    // 🔥 SUBSCRIPTION PLAN
    if (mode === "subscription") {

      const session = await stripe.checkout.sessions.create({
        mode: "subscription",
        payment_method_types: ["card"],

        line_items: [
          {
            price: "price_XXXXXXXX", // 👈 YOUR STRIPE PRICE ID
            quantity: 1
          }
        ],

        success_url: "https://cyberclinicsaas.com/dashboard",
        cancel_url: "https://cyberclinicsaas.com/pricing"
      });

      return res.json({ url: session.url });
    }

    // 🔥 ONE-TIME REPORT PAYMENT
    if (mode === "report") {

      const session = await stripe.checkout.sessions.create({
        mode: "payment",
        payment_method_types: ["card"],

        line_items: [
          {
            price_data: {
              currency: "usd",
              product_data: {
                name: "HIPAA Compliance Report"
              },
              unit_amount: 4900
            },
            quantity: 1
          }
        ],

        success_url: "https://cyberclinicsaas.com/dashboard",
        cancel_url: "https://cyberclinicsaas.com/dashboard"
      });

      return res.json({ url: session.url });
    }

  } catch (err) {
    console.error(err);
    res.status(500).send("Stripe error");
  }

});

export default router;