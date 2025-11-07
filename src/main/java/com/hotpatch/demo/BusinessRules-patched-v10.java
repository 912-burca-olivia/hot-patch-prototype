package com.hotpatch.demo;

/**
 * Business rules class - PATCHED VERSION
 * Updated version: More sophisticated tiered discount + bug fix
 */
public class BusinessRules {
    
    public double calculateDiscount(double amount) {
        // Updated business rule 
        if (amount > 200) {
            return 15.0;
        }
        return 2.5; // CHANGED
        
    }
    
    public String getRuleVersion() {
        return "v10.0-patched";
    }
}
