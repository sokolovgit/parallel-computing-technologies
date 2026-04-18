package ua.kpi.lab8.model;

public class MultiplyResponse {
    private double[][] result;
    private long computationTimeMs;
    private int matrixSize;
    private int gridSize;
    private int threadsUsed;
    private String dataSource;

    public MultiplyResponse() {
    }

    public MultiplyResponse(double[][] result, long computationTimeMs, int matrixSize, int gridSize, int threadsUsed, String dataSource) {
        this.result = result;
        this.computationTimeMs = computationTimeMs;
        this.matrixSize = matrixSize;
        this.gridSize = gridSize;
        this.threadsUsed = threadsUsed;
        this.dataSource = dataSource;
    }

    public double[][] getResult() {
        return result;
    }

    public void setResult(double[][] result) {
        this.result = result;
    }

    public long getComputationTimeMs() {
        return computationTimeMs;
    }

    public void setComputationTimeMs(long computationTimeMs) {
        this.computationTimeMs = computationTimeMs;
    }

    public int getMatrixSize() {
        return matrixSize;
    }

    public void setMatrixSize(int matrixSize) {
        this.matrixSize = matrixSize;
    }

    public int getGridSize() {
        return gridSize;
    }

    public void setGridSize(int gridSize) {
        this.gridSize = gridSize;
    }

    public int getThreadsUsed() {
        return threadsUsed;
    }

    public void setThreadsUsed(int threadsUsed) {
        this.threadsUsed = threadsUsed;
    }

    public String getDataSource() {
        return dataSource;
    }

    public void setDataSource(String dataSource) {
        this.dataSource = dataSource;
    }
}
