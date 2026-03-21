package sequential;

import java.util.Arrays;
import matrix.MatrixMultiplier;

/** Classic sequential multiply; i–k–j loop order for row-major cache locality. */
public final class SequentialMultiplier implements MatrixMultiplier {

    @Override
    public void multiply(double[][] a, double[][] b, double[][] c) {
        int n = a.length;
        for (int i = 0; i < n; i++) {
            Arrays.fill(c[i], 0.0);
            for (int k = 0; k < n; k++) {
                double aik = a[i][k];
                for (int j = 0; j < n; j++) {
                    c[i][j] += aik * b[k][j];
                }
            }
        }
    }
}
