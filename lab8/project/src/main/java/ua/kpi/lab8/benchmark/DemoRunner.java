package ua.kpi.lab8.benchmark;

import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Map;

public class DemoRunner {

    private static final String BASE_URL = "http://localhost:8080/api/multiply";
    private static final HttpClient client = HttpClient.newHttpClient();
    private static final ObjectMapper mapper = new ObjectMapper();

    public static void main(String[] args) throws Exception {
        System.out.println("===================================================");
        System.out.println("Lab8 Demo: Testing Matrix Multiplication Endpoints");
        System.out.println("===================================================");
        System.out.println();

        healthCheck();
        serverSideDemo();
        clientSideDemo();

        System.out.println("===================================================");
        System.out.println("Demo complete! Check server console for benchmarks.");
        System.out.println("===================================================");
    }

    private static void healthCheck() throws Exception {
        System.out.println("1. Health check...");
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/health"))
                .GET()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("   " + response.body());
        System.out.println();
    }

    private static void serverSideDemo() throws Exception {
        System.out.println("2. Server-side multiplication (n=256, q=2)...");
        sendServerRequest(256, 2);
        System.out.println();

        System.out.println("3. Server-side multiplication (n=512, q=4)...");
        sendServerRequest(512, 4);
        System.out.println();

        System.out.println("4. Server-side multiplication (n=1024, q=8)...");
        sendServerRequest(1024, 8);
        System.out.println();
    }

    private static void clientSideDemo() throws Exception {
        System.out.println("5. Client-side multiplication (4x4 matrices, q=2)...");
        double[][] matrixA = {
                {1, 2, 3, 4},
                {5, 6, 7, 8},
                {9, 10, 11, 12},
                {13, 14, 15, 16}
        };
        double[][] matrixB = {
                {1, 0, 0, 0},
                {0, 1, 0, 0},
                {0, 0, 1, 0},
                {0, 0, 0, 1}
        };
        sendClientRequest(matrixA, matrixB, 2);
        System.out.println();

        System.out.println("6. Client-side multiplication (8x8 matrices, q=4)...");
        double[][] matrixA8 = new double[8][8];
        double[][] matrixB8 = new double[8][8];
        for (int i = 0; i < 8; i++) {
            for (int j = 0; j < 8; j++) {
                matrixA8[i][j] = i + j + 1;
                matrixB8[i][j] = (i == j) ? 1 : 0;
            }
        }
        sendClientRequest(matrixA8, matrixB8, 4);
        System.out.println();
    }

    private static void sendServerRequest(int n, int q) throws Exception {
        Map<String, Integer> requestBody = Map.of("n", n, "q", q);
        String json = mapper.writeValueAsString(requestBody);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/server"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        Map<String, Object> result = mapper.readValue(response.body(), Map.class);

        System.out.printf("   Time: %sms, Size: %s, Grid: %s, Threads: %s, Source: %s%n",
                result.get("computationTimeMs"),
                result.get("matrixSize"),
                result.get("gridSize"),
                result.get("threadsUsed"),
                result.get("dataSource"));
    }

    private static void sendClientRequest(double[][] matrixA, double[][] matrixB, int q) throws Exception {
        Map<String, Object> requestBody = Map.of(
                "matrixA", matrixA,
                "matrixB", matrixB,
                "q", q
        );
        String json = mapper.writeValueAsString(requestBody);

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(BASE_URL + "/client"))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(json))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        Map<String, Object> result = mapper.readValue(response.body(), Map.class);

        System.out.printf("   Time: %sms, Size: %s, Grid: %s, Threads: %s, Source: %s%n",
                result.get("computationTimeMs"),
                result.get("matrixSize"),
                result.get("gridSize"),
                result.get("threadsUsed"),
                result.get("dataSource"));
    }
}
