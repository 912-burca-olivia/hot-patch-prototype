package com.hotpatch.demo;

import java.net.HttpURLConnection;
import java.net.URL;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.Random;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Load generator to simulate production traffic
 */
public class LoadGenerator {
    private static final String BASE_URL = "http://localhost:8080/api/discount";
    private static final AtomicLong totalRequests = new AtomicLong(0);
    private static final AtomicLong successfulRequests = new AtomicLong(0);
    private static final AtomicLong failedRequests = new AtomicLong(0);
    private static volatile boolean running = true;
    
    public static void main(String[] args) throws InterruptedException {
        int threadCount = 5; // Number of concurrent clients
        int requestsPerSecond = 10; // Total RPS across all threads
        
        if (args.length > 0) {
            threadCount = Integer.parseInt(args[0]);
        }
        if (args.length > 1) {
            requestsPerSecond = Integer.parseInt(args[1]);
        }
        
        System.out.println("=== Load Generator Started ===");
        System.out.println("Threads: " + threadCount);
        System.out.println("Target RPS: " + requestsPerSecond);
        System.out.println("Press Ctrl+C to stop");
        System.out.println();
        
        // Add shutdown hook
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            running = false;
            System.out.println("\n=== Final Statistics ===");
            printStats();
        }));
        
        ExecutorService executor = Executors.newFixedThreadPool(threadCount);
        Random random = new Random();
        
        long delayMs = 1000 / requestsPerSecond;
        
        // Start statistics printer
        Thread statsThread = new Thread(() -> {
            while (running) {
                try {
                    Thread.sleep(5000);
                    printStats();
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        statsThread.setDaemon(true);
        statsThread.start();
        
        // Generate load
        while (running) {
            executor.submit(() -> makeRequest(random));
            Thread.sleep(delayMs);
        }
        
        executor.shutdown();
        executor.awaitTermination(5, TimeUnit.SECONDS);
    }
    
    private static void makeRequest(Random random) {
        try {
            double amount = 50 + random.nextDouble() * 550; // $50-$600
            URL url = new URL(BASE_URL + "?amount=" + String.format("%.2f", amount));
            
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(2000);
            conn.setReadTimeout(2000);
            
            int responseCode = conn.getResponseCode();
            
            if (responseCode == 200) {
                BufferedReader in = new BufferedReader(
                    new InputStreamReader(conn.getInputStream())
                );
                in.lines().forEach(line -> {}); // Consume response
                in.close();
                successfulRequests.incrementAndGet();
            } else {
                failedRequests.incrementAndGet();
            }
            
            totalRequests.incrementAndGet();
            conn.disconnect();
            
        } catch (Exception e) {
            failedRequests.incrementAndGet();
            totalRequests.incrementAndGet();
        }
    }
    
    private static void printStats() {
        long total = totalRequests.get();
        long success = successfulRequests.get();
        long failed = failedRequests.get();
        double successRate = total > 0 ? (success * 100.0 / total) : 0;
        
        System.out.println(String.format(
            "[Stats] Total: %d | Success: %d | Failed: %d | Success Rate: %.2f%%",
            total, success, failed, successRate
        ));
    }
}