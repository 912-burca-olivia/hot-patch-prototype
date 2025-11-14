package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION (v11 heavy, hot-swap legal)
 * Same public API as original:
 *   - double calculateDiscount(double amount)
 *   - String getRuleVersion()
 * No new methods/fields are added (JVM redefineClasses restriction).
 */
public class BusinessRules {

    public double calculateDiscount(double amount) {
        // Keep a tiny, simple "base tier" inline (no new helper methods).
        double out = 1.0;
        if (amount > 1000) out = 15.0;
        else if (amount > 500) out = 10.0;
        else if (amount > 200) out = 6.0;
        else if (amount > 100) out = 3.0;

        // --- HEAVY WORK INLINE (still just changes the implementation) ---
        // We intentionally bloat the method body while staying under the
        // 64KB per-method bytecode limit (loops compile to small bytecode).
        double acc = 0.0;
        for (int i = 1; i <= 100_000; i++) {
            double x = (amount + i) * 0.00012345;
            // inline a few math transforms (no extra methods)
            double a = x * x * 0.37 - x * 0.11 + Math.sin(x * 2.0);
            double b = Math.cos(x * 0.5) + Math.tan((x + i) * 1e-3) * 0.01;
            double c = (i % 3 == 0) ? (a - b * 0.7) : (a + b * 0.4);
            acc += c * (1.0 + (i % 5) * 0.003);

            if ((i & 0xFF) == 0) {
                double t = Math.tanh(acc * 1e-3);
                double s = (acc >= 0) ? Math.sqrt(1.0 + t * t) : -Math.sqrt(1.0 + t * t);
                acc = s * 10.0 + (acc * 0.0001);
            }
        }

        double acc2 = 0.0;
        for (int i = 0; i < 1000; i++) {
            double inner = 0.0;
            for (int j = 1; j <= 50; j++) {
                double y = (i * 31 + j * 17) * 1e-4;
                inner += (y * y * 0.75) - (y * 0.33) + Math.sin(y * 12.34);
            }
            if ((i % 7) == 0) {
                double lo = -3.0, hi = 3.0;
                double clamped = inner < lo ? lo : (inner > hi ? hi : inner);
                inner = -inner * 0.5 + clamped;
            }
            acc2 += inner;
        }

        // Combine, then bound to 0..20 (percent-like)
        double combined = out + (acc * 0.0000004) + (acc2 * 0.002);
        if (combined < 0.0) combined = 0.0;
        if (combined > 20.0) combined = 20.0;

        return Math.round(combined * 10.0) / 10.0;
    }

    public String getRuleVersion() {
        return "v11.0-patched-heavy";
    }
}
