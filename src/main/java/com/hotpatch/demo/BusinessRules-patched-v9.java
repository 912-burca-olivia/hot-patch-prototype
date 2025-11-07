package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule 
        if (amount > 500) {
            return 35.0;
        }
        return 12.5; // CHANGED
        
    }
    
    public String getRuleVersion() {
        return "v9.0-patched";
    }
}
