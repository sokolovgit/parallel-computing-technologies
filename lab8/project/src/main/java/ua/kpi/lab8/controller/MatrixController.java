package ua.kpi.lab8.controller;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import ua.kpi.lab8.model.ClientMultiplyRequest;
import ua.kpi.lab8.model.MultiplyResponse;
import ua.kpi.lab8.model.ServerMultiplyRequest;
import ua.kpi.lab8.service.MatrixService;

@RestController
@RequestMapping("/api/multiply")
public class MatrixController {

    private final MatrixService matrixService;

    public MatrixController(MatrixService matrixService) {
        this.matrixService = matrixService;
    }

    @PostMapping("/server")
    public ResponseEntity<MultiplyResponse> multiplyServerSide(@RequestBody ServerMultiplyRequest request) {
        try {
            MultiplyResponse response = matrixService.multiplyServerSide(request.getN(), request.getQ());
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @PostMapping("/client")
    public ResponseEntity<MultiplyResponse> multiplyClientSide(@RequestBody ClientMultiplyRequest request) {
        try {
            MultiplyResponse response = matrixService.multiplyClientSide(
                    request.getMatrixA(), 
                    request.getMatrixB(), 
                    request.getQ()
            );
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().build();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("Matrix Multiplication Server is running");
    }
}
