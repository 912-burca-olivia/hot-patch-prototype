package com.hotpatch.tool;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

/** Posts to the agent's /rollback endpoint and prints latency. */
public class RollbackApplier {
    public static void main(String[] args) {
        String endpoint = (args.length >= 1) ? args[0] : "http://127.0.0.1:8088/rollback";
        try {
            HttpClient client = HttpClient.newHttpClient();
            HttpRequest req = HttpRequest.newBuilder(URI.create(endpoint))
                    .POST(HttpRequest.BodyPublishers.noBody())
                    .build();

            long t0 = System.nanoTime();
            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString());
            long t1 = System.nanoTime();
            double totalMs = (t1 - t0) / 1_000_000.0;

            System.out.println("HTTP " + resp.statusCode() + " from agent: " + resp.body());
            System.out.printf("Request→response latency: %.3f ms%n", totalMs);

            System.out.println(String.format("METRIC client_ms=%.3f agent_ms=%s", totalMs, resp.body().replace("OK","").replace("(rollback)","").replace("ms","").trim()));

            if (resp.statusCode() != 200) System.exit(2);
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }
}
