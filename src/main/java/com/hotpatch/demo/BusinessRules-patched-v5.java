package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule 
        if (amount > 500) {
            return 5.0;
        }
        return 1.5; // CHANGED
        
    }
    
    public String getRuleVersion() {
        return "v5.0-patched";
    }
}
