package ua.kpi.lab8;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {

    public static void main(String[] args) {
        System.out.println("=================================================");
        System.out.println("Lab8: Matrix Multiplication Server (Fox Algorithm)");
        System.out.println("=================================================");
        SpringApplication.run(Application.class, args);
    }
}
