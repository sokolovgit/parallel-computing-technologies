package lab4.task2;

import java.util.concurrent.RecursiveAction;

/**
 * Стрічкове множення C = A·B: кожен рядок C — скалярний добуток рядка A на стовпці B.
 * Рекурсивно ділить діапазон рядків [rowStart, rowEnd) доки не стане не більшим за leafRows.
 */
public final class StripedMatMulTask extends RecursiveAction {

    private final double[][] a;
    private final double[][] b;
    private final double[][] c;
    private final int rowStart;
    private final int rowEnd;
    private final int leafRows;

    public StripedMatMulTask(double[][] a, double[][] b, double[][] c, int rowStart, int rowEnd, int leafRows) {
        this.a = a;
        this.b = b;
        this.c = c;
        this.rowStart = rowStart;
        this.rowEnd = rowEnd;
        this.leafRows = leafRows;
    }

    @Override
    protected void compute() {
        int n = rowEnd - rowStart;
        if (n <= leafRows) {
            multiplyRowRange(rowStart, rowEnd);
            return;
        }
        int mid = rowStart + n / 2;
        StripedMatMulTask left = new StripedMatMulTask(a, b, c, rowStart, mid, leafRows);
        StripedMatMulTask right = new StripedMatMulTask(a, b, c, mid, rowEnd, leafRows);
        left.fork();
        right.compute();
        left.join();
    }

    private void multiplyRowRange(int rs, int re) {
        int dim = a.length;
        for (int i = rs; i < re; i++) {
            for (int j = 0; j < dim; j++) {
                double sum = 0.0;
                for (int k = 0; k < dim; k++) {
                    sum += a[i][k] * b[k][j];
                }
                c[i][j] = sum;
            }
        }
    }
}
