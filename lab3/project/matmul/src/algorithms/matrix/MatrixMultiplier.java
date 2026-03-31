package matrix;

/**
 * Square matrix multiply {@code C = A &times; B} into {@code c}. Parallel implementations may use
 * multiple threads; {@link InterruptedException} is declared for compatibility with those paths.
 */
@FunctionalInterface
public interface MatrixMultiplier {

    void multiply(double[][] a, double[][] b, double[][] c) throws InterruptedException;
}
