package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule 
        if (amount > 300) {
            return 3.0;
        }
        return 0.0; // CHANGED
        
    }
    
    public String getRuleVersion() {
        return "v6.0-patched";
    }
}
