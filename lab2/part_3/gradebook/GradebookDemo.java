package part_3.gradebook;

/**
 * Runs the electronic gradebook: one lecturer and three assistants assign
 * grades concurrently; after they finish, the grade table is printed.
 */
public class GradebookDemo {

    public static final int STUDENTS_PER_GROUP = 5;
    public static final int WEEKS_COUNT = 4;

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Electronic gradebook: 1 lecturer + 3 assistants");
        System.out.println("3 groups, " + STUDENTS_PER_GROUP + " students per group, " + WEEKS_COUNT + " weeks");
        System.out.println("Grades 0–100. All four threads write concurrently (ReentrantLock).\n");

        Gradebook gradebook = new Gradebook(STUDENTS_PER_GROUP, WEEKS_COUNT);

        LecturerThread lecturer = new LecturerThread(gradebook);
        AssistantThread assistant0 = new AssistantThread(gradebook, 0);
        AssistantThread assistant1 = new AssistantThread(gradebook, 1);
        AssistantThread assistant2 = new AssistantThread(gradebook, 2);

        lecturer.start();
        assistant0.start();
        assistant1.start();
        assistant2.start();

        lecturer.join();
        assistant0.join();
        assistant1.join();
        assistant2.join();

        System.out.println(gradebook.formatTable());
    }
}
