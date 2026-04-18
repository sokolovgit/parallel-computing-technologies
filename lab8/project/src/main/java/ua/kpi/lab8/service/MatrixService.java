package ua.kpi.lab8.service;

import org.springframework.stereotype.Service;
import ua.kpi.lab8.algorithm.FoxParallelMultiplier;
import ua.kpi.lab8.model.MultiplyResponse;

import java.util.Random;

@Service
public class MatrixService {

    private final Random random = new Random();

    public MultiplyResponse multiplyServerSide(int n, int q) throws InterruptedException {
        double[][] matrixA = generateRandomMatrix(n);
        double[][] matrixB = generateRandomMatrix(n);
        
        return multiplyMatrices(matrixA, matrixB, q, "server");
    }

    public MultiplyResponse multiplyClientSide(double[][] matrixA, double[][] matrixB, int q) throws InterruptedException {
        validateMatrices(matrixA, matrixB);
        return multiplyMatrices(matrixA, matrixB, q, "client");
    }

    private MultiplyResponse multiplyMatrices(double[][] matrixA, double[][] matrixB, int q, String dataSource) throws InterruptedException {
        int n = matrixA.length;
        double[][] result = new double[n][n];
        
        FoxParallelMultiplier multiplier = new FoxParallelMultiplier(q);
        
        long startTime = System.currentTimeMillis();
        multiplier.multiply(matrixA, matrixB, result);
        long endTime = System.currentTimeMillis();
        
        long computationTime = endTime - startTime;
        int threadsUsed = multiplier.getWorkerCount();
        
        logStatistics(n, q, threadsUsed, computationTime, dataSource);
        
        return new MultiplyResponse(result, computationTime, n, q, threadsUsed, dataSource);
    }

    private void logStatistics(int n, int q, int threads, long timeMs, String dataSource) {
        long operations = (long) n * n * n;
        double opsPerSecond = (operations / (timeMs / 1000.0));
        String opsFormatted = formatOps(opsPerSecond);
        
        System.out.printf("[BENCHMARK] %s-side | n=%d | q=%d | threads=%d | time=%dms | ops=%s%n",
                capitalizeFirst(dataSource), n, q, threads, timeMs, opsFormatted);
    }

    private String formatOps(double opsPerSecond) {
        if (opsPerSecond >= 1_000_000_000) {
            return String.format("%.2fG/s", opsPerSecond / 1_000_000_000);
        } else if (opsPerSecond >= 1_000_000) {
            return String.format("%.2fM/s", opsPerSecond / 1_000_000);
        } else if (opsPerSecond >= 1_000) {
            return String.format("%.2fK/s", opsPerSecond / 1_000);
        } else {
            return String.format("%.2f/s", opsPerSecond);
        }
    }

    private String capitalizeFirst(String str) {
        if (str == null || str.isEmpty()) {
            return str;
        }
        return str.substring(0, 1).toUpperCase() + str.substring(1);
    }

    private double[][] generateRandomMatrix(int n) {
        double[][] matrix = new double[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                matrix[i][j] = random.nextDouble() * 10;
            }
        }
        return matrix;
    }

    private void validateMatrices(double[][] matrixA, double[][] matrixB) {
        if (matrixA == null || matrixB == null) {
            throw new IllegalArgumentException("Matrices cannot be null");
        }
        if (matrixA.length == 0 || matrixB.length == 0) {
            throw new IllegalArgumentException("Matrices cannot be empty");
        }
        if (matrixA.length != matrixA[0].length || matrixB.length != matrixB[0].length) {
            throw new IllegalArgumentException("Matrices must be square");
        }
        if (matrixA.length != matrixB.length) {
            throw new IllegalArgumentException("Matrices must have the same dimensions");
        }
    }
}
