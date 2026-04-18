package ua.kpi.lab8.algorithm;

@FunctionalInterface
public interface MatrixMultiplier {

    void multiply(double[][] a, double[][] b, double[][] c) throws InterruptedException;
}
