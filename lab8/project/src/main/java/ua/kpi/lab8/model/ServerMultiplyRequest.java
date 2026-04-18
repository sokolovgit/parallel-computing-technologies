package ua.kpi.lab8.model;

public class ServerMultiplyRequest {
    private int n;
    private int q;

    public ServerMultiplyRequest() {
    }

    public ServerMultiplyRequest(int n, int q) {
        this.n = n;
        this.q = q;
    }

    public int getN() {
        return n;
    }

    public void setN(int n) {
        this.n = n;
    }

    public int getQ() {
        return q;
    }

    public void setQ(int q) {
        this.q = q;
    }
}
