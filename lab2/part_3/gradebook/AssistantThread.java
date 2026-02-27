package part_3.gradebook;

import java.util.Random;

/**
 * Thread representing one assistant: assigns grades for a single group
 * (all students, all weeks). Assistant index 0 -> group 0, etc.
 */
public class AssistantThread extends Thread {

    private final Gradebook gradebook;
    private final int assistantIndex;
    private final Random rnd = new Random();

    public AssistantThread(Gradebook gradebook, int assistantIndex) {
        this.gradebook = gradebook;
        this.assistantIndex = assistantIndex;
    }

    @Override
    public void run() {
        int group = assistantIndex;
        if (group >= Gradebook.NUM_GROUPS) {
            return;
        }
        for (int week = 0; week < gradebook.getWeeksCount(); week++) {
            for (int student = 0; student < gradebook.getStudentsPerGroup(); student++) {
                int grade = 50 + rnd.nextInt(51); // 50–100
                gradebook.setGrade(group, student, week, grade);
            }
        }
    }
}
