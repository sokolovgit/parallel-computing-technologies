package src.bounce;

public class BallThread extends Thread {

    private Ball ball;
    private BallCanvas canvas;

    public BallThread(Ball ball, BallCanvas canvas) {
        this.ball = ball;
        this.canvas = canvas;
    }

    @Override
    public void run() {
        try {
            for (int i = 0; i < Config.BALL_MOVES_COUNT; i++) {

                ball.move();

                Thread.sleep(canvas.getSleepTime());

            }
        } catch (InterruptedException er) {
            er.printStackTrace();
        }
    }
}
