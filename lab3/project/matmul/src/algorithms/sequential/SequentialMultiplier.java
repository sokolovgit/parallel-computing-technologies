package sequential;

import matrix.MatrixMultiplier;

/** Sequential multiply (same structure as {@code DefaultMatrixMultiplication} in course reference). */
public final class SequentialMultiplier implements MatrixMultiplier {

    @Override
    public void multiply(double[][] a, double[][] b, double[][] c) {
        int n = a.length;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                double sum = 0.0;
                for (int k = 0; k < n; k++) {
                    sum += a[i][k] * b[k][j];
                }
                c[i][j] = sum;
            }
        }
    }
}
