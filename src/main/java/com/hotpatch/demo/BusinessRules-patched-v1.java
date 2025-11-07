package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule (v2) - More tiers + bug fix
        if (amount > 500) {
            return 25.0; // 25% discount for orders over $500
        } else if (amount > 200) {
            return 15.0; // 15% discount for orders over $200
        } else if (amount > 100) {
            return 10.0; // 10% discount for orders over $100
        }
        return 5.0; // CHANGED: Give everyone at least 5% (was 0%)
    }
    
    public String getRuleVersion() {
        return "v1.0-patched";
    }
}