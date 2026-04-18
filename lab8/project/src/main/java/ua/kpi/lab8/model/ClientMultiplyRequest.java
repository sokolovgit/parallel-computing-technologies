package ua.kpi.lab8.model;

public class ClientMultiplyRequest {
    private double[][] matrixA;
    private double[][] matrixB;
    private int q;

    public ClientMultiplyRequest() {
    }

    public ClientMultiplyRequest(double[][] matrixA, double[][] matrixB, int q) {
        this.matrixA = matrixA;
        this.matrixB = matrixB;
        this.q = q;
    }

    public double[][] getMatrixA() {
        return matrixA;
    }

    public void setMatrixA(double[][] matrixA) {
        this.matrixA = matrixA;
    }

    public double[][] getMatrixB() {
        return matrixB;
    }

    public void setMatrixB(double[][] matrixB) {
        this.matrixB = matrixB;
    }

    public int getQ() {
        return q;
    }

    public void setQ(int q) {
        this.q = q;
    }
}
