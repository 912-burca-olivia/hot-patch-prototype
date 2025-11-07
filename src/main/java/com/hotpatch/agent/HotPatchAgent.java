package com.hotpatch.agent;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.instrument.ClassDefinition;
import java.lang.instrument.Instrumentation;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.ArrayDeque;
import java.util.Deque;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;

public class HotPatchAgent {
    private static Instrumentation instrumentation;

    private static final String TARGET_CLASS_NAME = "com.hotpatch.demo.BusinessRules";
    private static final int PORT = 8088; // localhost only

    // Version tracking (latest-only rollback)
    private static volatile boolean httpStarted = false;
    private static volatile byte[] currentBytes = null;  // bytes of current active version
    private static final Deque<byte[]> history = new ArrayDeque<>(); // previous versions (top = last)

    // Called when agent is loaded at JVM startup
    public static void premain(String agentArgs, Instrumentation inst) {
        instrumentation = inst;
        System.out.println("[HotPatchAgent] Agent loaded at startup");
        // Try to capture baseline bytes from classpath resource (demo-friendly)
        tryInitBaselineBytes();
        startHttp();
    }

    // Called when agent is attached to running JVM
    public static void agentmain(String agentArgs, Instrumentation inst) {
        instrumentation = inst;
        System.out.println("[HotPatchAgent] Agent attached to running JVM");
        tryInitBaselineBytes();
        startHttp();
        if (agentArgs != null && !agentArgs.isEmpty()) {
            try {
                // Back-compat: still allow path-based patch if someone uses dynamic attach
                byte[] bytes = java.nio.file.Files.readAllBytes(java.nio.file.Path.of(agentArgs));
                double lat = applyPatchBytes(bytes, "file:" + agentArgs);
            } catch (Exception e) {
                System.err.println("[HotPatchAgent] Failed to apply patch: " + e);
                e.printStackTrace();
            }
        }
    }

    private static synchronized void startHttp() {
        if (httpStarted) return;
        try {
            HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", PORT), 0);
            server.createContext("/patch", HotPatchAgent::handlePatch);
            server.createContext("/rollback", HotPatchAgent::handleRollback);
            server.setExecutor(null);
            server.start();
            httpStarted = true;
            System.out.println("[HotPatchAgent] HTTP control listening at http://127.0.0.1:" + PORT + "/patch");
        } catch (IOException e) {
            System.err.println("[HotPatchAgent] Failed to start HTTP control: " + e);
        }
    }

    // ---- HTTP handlers ----

    private static void handlePatch(HttpExchange ex) throws IOException {
        if (!"POST".equalsIgnoreCase(ex.getRequestMethod())) {
            ex.sendResponseHeaders(405, -1);
            return;
        }
        byte[] body = ex.getRequestBody().readAllBytes();
        if (body.length == 0) {
            respond(ex, 400, "empty body");
            return;
        }
        try {
            // Preserve your printing/latency semantics:
            System.out.println("[HotPatchAgent] Reading patched class from: HTTP body (" + body.length + " bytes)");
            double latencyMs = applyPatchBytes(body, "http-body");
            respond(ex, 200, String.format("OK %.3f ms", latencyMs));
        } catch (Throwable t) {
            t.printStackTrace();
            respond(ex, 500, "ERROR: " + t);
        }
    }

    private static void handleRollback(HttpExchange ex) throws IOException {
        if (!"POST".equalsIgnoreCase(ex.getRequestMethod())) {
            ex.sendResponseHeaders(405, -1);
            return;
        }
        if (history.isEmpty()) {
            respond(ex, 409, "no previous version to rollback to");
            return;
        }
        try {
            byte[] prev = history.pop();
            long startTime = System.nanoTime();

            Class<?> targetClass = findTargetClass();
            System.out.println("[HotPatchAgent] Found target class: " + targetClass.getName());
            instrumentation.redefineClasses(new ClassDefinition(targetClass, prev));

            long endTime = System.nanoTime();
            double latencyMs = (endTime - startTime) / 1_000_000.0;

            currentBytes = prev;

            System.out.println("[HotPatchAgent] ✓ Patch applied successfully!");
            System.out.println("[HotPatchAgent] Latency: " + String.format("%.3f", latencyMs) + " ms");
            System.out.println("[HotPatchAgent] Class redefined: " + TARGET_CLASS_NAME);

            respond(ex, 200, "OK " + String.format("%.3f ms (rollback)", latencyMs));
        } catch (Throwable t) {
            t.printStackTrace();
            respond(ex, 500, "ERROR: " + t);
        }
    }

    // ---- Core helpers ----

    private static double applyPatchBytes(byte[] newBytes, String srcHint) throws Exception {
        long startTime = System.nanoTime();

        Class<?> targetClass = findTargetClass();
        System.out.println("[HotPatchAgent] Found target class: " + targetClass.getName());

        // Save current version for rollback
        if (currentBytes != null) {
            history.push(currentBytes);
        }
        // Apply new version
        instrumentation.redefineClasses(new ClassDefinition(targetClass, newBytes));
        currentBytes = newBytes;

        long endTime = System.nanoTime();
        double latencyMs = (endTime - startTime) / 1_000_000.0;

        System.out.println("[HotPatchAgent] ✓ Patch applied successfully!");
        System.out.println("[HotPatchAgent] Latency: " + String.format("%.3f", latencyMs) + " ms");
        System.out.println("[HotPatchAgent] Class redefined: " + TARGET_CLASS_NAME);

        return latencyMs;
    }

    private static Class<?> findTargetClass() throws ClassNotFoundException {
        Class<?> targetClass = null;
        for (Class<?> c : instrumentation.getAllLoadedClasses()) {
            if (c.getName().equals(TARGET_CLASS_NAME)) { targetClass = c; break; }
        }
        if (targetClass == null) throw new ClassNotFoundException("Target class not loaded: " + TARGET_CLASS_NAME);
        return targetClass;
    }

    private static void tryInitBaselineBytes() {
        if (currentBytes != null) return;
        // Try to read the original bytes from the classpath resource
        String res = TARGET_CLASS_NAME.replace('.', '/') + ".class";
        try (InputStream in = HotPatchAgent.class.getClassLoader().getResourceAsStream(res)) {
            if (in != null) {
                currentBytes = in.readAllBytes();
                // No print needed; keep logs clean
            }
        } catch (IOException ignored) {}
    }

    private static void respond(HttpExchange ex, int code, String msg) throws IOException {
        byte[] out = msg.getBytes(StandardCharsets.UTF_8);
        ex.getResponseHeaders().add("Content-Type", "text/plain; charset=utf-8");
        ex.sendResponseHeaders(code, out.length);
        try (OutputStream os = ex.getResponseBody()) { os.write(out); }
    }

    public static Instrumentation getInstrumentation() { return instrumentation; }
}
