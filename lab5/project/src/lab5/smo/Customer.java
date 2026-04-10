package lab5.smo;

/** Customer request in the queueing system (id for tracing). */
final class Customer {

    private final long id;

    Customer(long id) {
        this.id = id;
    }

    long id() {
        return id;
    }
}
