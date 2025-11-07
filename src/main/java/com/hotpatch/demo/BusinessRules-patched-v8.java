package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule 
        if (amount > 1500) {
            return 25.0;
        }
        return 2.5; // CHANGED
        
    }
    
    public String getRuleVersion() {
        return "v8.0-patched";
    }
}
