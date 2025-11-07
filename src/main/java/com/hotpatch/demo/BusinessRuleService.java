package com.hotpatch.demo;

import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpExchange;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Main business service with rules that can be hot-patched
 */
public class BusinessRuleService {
    private static final AtomicLong requestCount = new AtomicLong(0);
    private static volatile String currentVersion = "v1.0";
    
    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
        
        // Business rule endpoint
        server.createContext("/api/discount", new DiscountHandler());
        
        // Health check endpoint
        server.createContext("/api/health", exchange -> {
            String response = "OK - Version: " + currentVersion;
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        });
        
        // Verification endpoint
        server.createContext("/api/verify", exchange -> {
            BusinessRules rules = new BusinessRules();
            double testDiscount = rules.calculateDiscount(150.0);
            String version = rules.getRuleVersion();
            
            String response = String.format(
                "Rule Version: %s\nTest Amount: $150.00\nDiscount: %.2f%%\nTotal Requests: %d",
                version, testDiscount, requestCount.get()
            );
            
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        });
        
        server.setExecutor(null);
        server.start();
        System.out.println("Business Rule Service started on port 8080");
        System.out.println("Endpoints:");
        System.out.println("  - http://localhost:8080/api/discount?amount=100");
        System.out.println("  - http://localhost:8080/api/health");
        System.out.println("  - http://localhost:8080/api/verify");
    }
    
    static class DiscountHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            requestCount.incrementAndGet();
            
            String query = exchange.getRequestURI().getQuery();
            double amount = 100.0;
            
            if (query != null && query.startsWith("amount=")) {
                try {
                    amount = Double.parseDouble(query.substring(7));
                } catch (NumberFormatException e) {
                    amount = 100.0;
                }
            }
            
            BusinessRules rules = new BusinessRules();
            double discount = rules.calculateDiscount(amount);
            
            String response = String.format(
                "Amount: $%.2f\nDiscount: %.2f%%\nRule Version: %s",
                amount, discount, rules.getRuleVersion()
            );
            
            exchange.sendResponseHeaders(200, response.length());
            OutputStream os = exchange.getResponseBody();
            os.write(response.getBytes());
            os.close();
        }
    }
}