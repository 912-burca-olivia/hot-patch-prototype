package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule 
        if (amount > 1000) {
            return 12.0;
        }
        return 1.0; // CHANGED
        
    }
    
    public String getRuleVersion() {
        return "v4.0-patched";
    }
}
