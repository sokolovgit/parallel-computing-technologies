package part_1.bank;

class TransferThread extends Thread {

    private final Bank bank;
    private final int fromAccount;
    private final int maxAmount;
    private final int reps;

    TransferThread(Bank bank, int from, int maxAmount, int reps) {
        this.bank = bank;
        this.fromAccount = from;
        this.maxAmount = maxAmount;
        this.reps = reps;
    }

    @Override
    public void run() {
        for (int i = 0; i < reps; i++) {
            int toAccount = (int) (bank.size() * Math.random());
            int amount = (int) (maxAmount * Math.random() / 10);
            bank.transfer(fromAccount, toAccount, amount);
        }
    }
}

