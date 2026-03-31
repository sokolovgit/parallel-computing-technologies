package utils;

public final class MatrixTestData {

    private MatrixTestData() {}

    public static void fillDeterministic(double[][] a, double[][] b) {
        int n = a.length;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                a[i][j] = (i + 1) * 0.01 + (j + 1) * 0.001;
                b[i][j] = (i * n + j) * 0.0001 + 1.0;
            }
        }
    }

    public static void assertClose(double[][] expected, double[][] actual, int n, String label) {
        double eps = 1e-8;
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                double d = Math.abs(expected[i][j] - actual[i][j]);
                if (d > eps) {
                    throw new AssertionError(
                            label + " mismatch at (" + i + "," + j + "): " + expected[i][j] + " vs " + actual[i][j]);
                }
            }
        }
    }
}
