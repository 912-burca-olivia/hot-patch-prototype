package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule (v4)
        if (amount > 1000) {
            return 23.0;
        }
        return 7.0; // CHANGED: Give everyone at least 7%
        
    }
    
    public String getRuleVersion() {
        return "v3.0-patched";
    }
}
