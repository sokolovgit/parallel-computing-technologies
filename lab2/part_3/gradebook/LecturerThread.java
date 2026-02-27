package part_3.gradebook;

import java.util.Random;

/**
 * Thread representing the lecturer: each week assigns a grade (0–100) to every
 * student in every group.
 */
public class LecturerThread extends Thread {

    private final Gradebook gradebook;
    private final Random rnd = new Random();

    public LecturerThread(Gradebook gradebook) {
        this.gradebook = gradebook;
    }

    @Override
    public void run() {
        for (int week = 0; week < gradebook.getWeeksCount(); week++) {
            for (int group = 0; group < Gradebook.NUM_GROUPS; group++) {
                for (int student = 0; student < gradebook.getStudentsPerGroup(); student++) {
                    int grade = 60 + rnd.nextInt(41); // 60–100
                    gradebook.setGrade(group, student, week, grade);
                }
            }
        }
    }
}
