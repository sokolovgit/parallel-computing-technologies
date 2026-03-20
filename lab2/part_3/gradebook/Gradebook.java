package part_3.gradebook;

import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

/**
 * Electronic gradebook: grades for one discipline, 3 groups of students, by week.
 * Grades are on a 0–100 scale. All updates are protected by a single lock
 * so that lecturer and assistants can write concurrently without lost updates.
 */
public class Gradebook {

    public static final int NUM_GROUPS = 3;
    public static final int MIN_GRADE = 0;
    public static final int MAX_GRADE = 100;

    private final int studentsPerGroup;
    private final int weeksCount;
    /** grades[group][student][week] */
    private final int[][][] grades;
    private final Lock lock = new ReentrantLock();

    public Gradebook(int studentsPerGroup, int weeksCount) {
        this.studentsPerGroup = studentsPerGroup;
        this.weeksCount = weeksCount;
        this.grades = new int[NUM_GROUPS][studentsPerGroup][weeksCount];
    }

    public void setGrade(int group, int student, int week, int value) {
        if (group < 0 || group >= NUM_GROUPS || student < 0 || student >= studentsPerGroup
                || week < 0 || week >= weeksCount) {
            return;
        }
        int grade = Math.max(MIN_GRADE, Math.min(MAX_GRADE, value));
        lock.lock();
        try {
            grades[group][student][week] = grade;
        } finally {
            lock.unlock();
        }
    }

    public int getGrade(int group, int student, int week) {
        lock.lock();
        try {
            return grades[group][student][week];
        } finally {
            lock.unlock();
        }
    }

    public int getStudentsPerGroup() {
        return studentsPerGroup;
    }

    public int getWeeksCount() {
        return weeksCount;
    }

    /** Builds a string table of all grades and group averages. */
    public String formatTable() {
        lock.lock();
        try {
            StringBuilder sb = new StringBuilder();
            sb.append("Electronic gradebook (3 groups, ").append(studentsPerGroup)
                    .append(" students, ").append(weeksCount).append(" weeks)\n\n");

            for (int g = 0; g < NUM_GROUPS; g++) {
                sb.append("--- Group ").append(g + 1).append(" ---\n");
                sb.append("Student   ");
                for (int w = 0; w < weeksCount; w++) {
                    sb.append(" Week").append(w + 1).append("  ");
                }
                sb.append(" Avg\n");

                long groupSum = 0;
                int groupCount = 0;
                for (int s = 0; s < studentsPerGroup; s++) {
                    sb.append(String.format("%4d      ", s + 1));
                    int rowSum = 0;
                    for (int w = 0; w < weeksCount; w++) {
                        int v = grades[g][s][w];
                        sb.append(String.format("%4d   ", v));
                        rowSum += v;
                        groupSum += v;
                        groupCount++;
                    }
                    double avg = weeksCount > 0 ? (double) rowSum / weeksCount : 0;
                    sb.append(String.format("  %5.1f\n", avg));
                }
                double groupAvg = groupCount > 0 ? (double) groupSum / groupCount : 0;
                sb.append("Group avg: ").append(String.format("%.1f", groupAvg)).append("\n\n");
            }
            return sb.toString();
        } finally {
            lock.unlock();
        }
    }
}
