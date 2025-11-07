package com.hotpatch.tool;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * PatchApplier: sends class bytes to the agent's HTTP control channel.
 *
 * Usage:
 *   java com.hotpatch.tool.PatchApplier target/classes-patched/com/hotpatch/demo/BusinessRules.class [http://127.0.0.1:8088/patch]
 */
public class PatchApplier {

    public static void main(String[] args) {
        if (args.length < 1) {
            System.out.println("Usage: java com.hotpatch.tool.PatchApplier <classFilePath> [endpoint]");
            System.out.println("Default endpoint: http://127.0.0.1:8088/patch");
            System.exit(1);
        }

        String classFilePath = args[0];
        String endpoint = (args.length >= 2) ? args[1] : "http://127.0.0.1:8088/patch";

        try {
            byte[] bytes = Files.readAllBytes(Path.of(classFilePath));

            HttpClient client = HttpClient.newHttpClient();
            HttpRequest req = HttpRequest.newBuilder(URI.create(endpoint))
                    .header("Content-Type", "application/octet-stream")
                    .POST(HttpRequest.BodyPublishers.ofByteArray(bytes))
                    .build();

            long t0 = System.nanoTime();
            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
            long t1 = System.nanoTime();

            double totalMs = (t1 - t0) / 1_000_000.0;

            System.out.println("HTTP " + resp.statusCode() + " from agent: " + resp.body());
            System.out.println(String.format("Request→response latency: %.3f ms", totalMs));

            System.out.println(String.format("METRIC client_ms=%.3f agent_ms=%s", totalMs, resp.body().replace("OK","").replace("ms","").trim()));

            if (resp.statusCode() != 200) System.exit(2);
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }
}
