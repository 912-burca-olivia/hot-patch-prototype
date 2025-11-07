package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule (v3)
        if (amount > 200) {
            return 10.0; // 15% discount for orders over $200
        } else if (amount > 100) {
            return 5.0; // 10% discount for orders over $100
        }
        return 3.0; // CHANGED: Give everyone at least 5% (was 0%)
    }
    
    public String getRuleVersion() {
        return "v2.0-patched";
    }
}