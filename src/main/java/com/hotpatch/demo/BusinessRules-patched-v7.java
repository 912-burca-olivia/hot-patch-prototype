package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule 
        if (amount > 1500) {
            return 20.0;
        }
        return 2.0; // CHANGED
        
    }
    
    public String getRuleVersion() {
        return "v7.0-patched";
    }
}
