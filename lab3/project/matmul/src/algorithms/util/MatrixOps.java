package util;

/** Helpers for preparing result buffers. */
public final class MatrixOps {

    private MatrixOps() {}

    public static void fillZero(double[][] c) {
        for (int i = 0; i < c.length; i++) {
            for (int j = 0; j < c[i].length; j++) {
                c[i][j] = 0.0;
            }
        }
    }
}
