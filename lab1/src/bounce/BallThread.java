package src.bounce;

public class BallThread extends Thread {
    private Ball ball;

    public BallThread(Ball ball) {
        this.ball = ball;
    }

    @Override
    public void run() {
        try {
            for (int i = 0; i < 10000; i++) {
                ball.move();
                System.out.println("Thread name = " + Thread.currentThread().getName());
                Thread.sleep(Config.SLEEP_MS);
            }
        } catch (InterruptedException ex) {
            ex.printStackTrace();
        }
    }
}