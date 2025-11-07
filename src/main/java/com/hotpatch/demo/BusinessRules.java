package com.hotpatch.demo;

/**
 * Business rules class - THIS WILL BE HOT-PATCHED
 * Original version: Simple tiered discount
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Original business rule (v1)
        if (amount > 100) {
            return 10.0; // 10% discount for orders over $100
        }
        return 0.0; // No discount
    }
    
    public String getRuleVersion() {
        return "v0.0-original";
    }
}