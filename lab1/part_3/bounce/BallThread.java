package part_3.bounce;

public class BallThread extends Thread {

    private final Ball ball;
    private final BallCanvas canvas;

    public BallThread(Ball ball, BallCanvas canvas, int priority) {
        this.ball = ball;
        this.canvas = canvas;
        setPriority(priority);
    }

    @Override
    public void run() {
        canvas.registerBallThread(this);
        try {
            for (int i = 0; i < Config.BALL_MOVES_COUNT; i++) {
                ball.move();
                Thread.sleep(canvas.getSleepTime());
            }
        } catch (InterruptedException er) {
            er.printStackTrace();
        }
        canvas.unregisterBallThread(this);
    }
}
