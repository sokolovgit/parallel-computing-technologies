# Lab8: Client-Server Matrix Multiplication

Matrix multiplication server using the Fox parallel algorithm with client-server architecture.

## Features

- **Server-side data**: Server generates random matrices
- **Client-side data**: Client provides matrices via HTTP
- **Fox parallel algorithm**: Efficient block-based multiplication with configurable grid size
- **Console statistics**: Real-time performance metrics
- **Benchmark suite**: Automated testing across multiple configurations

## Architecture

```
Client (HTTP) → Spring Boot Server → Fox Algorithm (q×q threads) → Results
```

## Requirements

- Java 17+
- Maven 3.6+

## Build

```bash
cd lab8/project-java
mvn clean package
```

## Run Server

Using justfile (recommended):
```bash
just server
```

Or using Maven directly:
```bash
mvn spring-boot:run
```

Server starts on `http://localhost:8080`

## Quick Commands (using justfile)

The project includes a justfile with convenient commands:

```bash
# Start the server
just server

# Run demo (tests both client and server endpoints)
just demo

# Run HTTP-based benchmarks
just benchmark

# Run standalone benchmarks (no HTTP)
just benchmark-standalone

# Build the project
just build
```

## API Endpoints

### 1. Server-Side Multiplication

Server generates random matrices:

```bash
curl -X POST http://localhost:8080/api/multiply/server \
  -H "Content-Type: application/json" \
  -d '{"n": 512, "q": 4}'
```

**Parameters:**
- `n`: Matrix size (must be divisible by q)
- `q`: Grid size (q×q threads will be used)

### 2. Client-Side Multiplication

Client provides matrices:

```bash
curl -X POST http://localhost:8080/api/multiply/client \
  -H "Content-Type: application/json" \
  -d '{
    "matrixA": [[1,2],[3,4]],
    "matrixB": [[5,6],[7,8]],
    "q": 2
  }'
```

**Parameters:**
- `matrixA`: First square matrix
- `matrixB`: Second square matrix
- `q`: Grid size

### 3. Health Check

```bash
curl http://localhost:8080/api/multiply/health
```

## Response Format

```json
{
  "result": [[...], [...]], 
  "computationTimeMs": 245,
  "matrixSize": 1024,
  "gridSize": 4,
  "threadsUsed": 16,
  "dataSource": "server"
}
```

## Console Statistics

Each computation logs performance metrics:

```
[BENCHMARK] Server-side | n=1024 | q=4 | threads=16 | time=245ms | ops=4.39M/s
[BENCHMARK] Client-side | n=512  | q=2 | threads=4  | time=89ms  | ops=1.52M/s
```

## Run Benchmarks

### Demo Mode (Quick Test)

Tests both server-side and client-side endpoints with example data:

```bash
just demo
```

This will:
1. Test health endpoint
2. Run server-side multiplications (n=256, 512, 1024)
3. Run client-side multiplications with small matrices
4. Display results with timing information

### HTTP Benchmarks (Full Suite)

Run comprehensive benchmarks via HTTP:

```bash
just benchmark
```

Tests configurations:
- Matrix sizes: 256, 512, 1024
- Grid sizes: 2, 4, 8
- 3 iterations per configuration
- Shows speedup analysis and throughput

### Standalone Benchmarks (No HTTP)

Run benchmarks without starting the HTTP server:

```bash
just benchmark-standalone
```

This tests the Fox algorithm directly without HTTP overhead.

## Performance Research

### Task 2: Benchmark Different Matrix Sizes

Compare performance across sizes and thread counts:

```bash
# Start server
mvn spring-boot:run

# In another terminal, test different sizes
for n in 256 512 1024; do
  for q in 2 4 8; do
    echo "Testing n=$n, q=$q"
    curl -X POST http://localhost:8080/api/multiply/server \
      -H "Content-Type: application/json" \
      -d "{\"n\": $n, \"q\": $q}"
    echo ""
  done
done
```

### Task 3: Compare with Lab7 MPI

Lab7 (MPI distributed) vs Lab8 (client-server multithreading):

| Aspect | Lab7 (MPI) | Lab8 (Client-Server) |
|--------|-----------|---------------------|
| Architecture | Distributed memory | Shared memory |
| Communication | MPI collectives | HTTP REST |
| Parallelism | Multiple processes/nodes | Multiple threads |
| Scalability | Horizontal (add nodes) | Vertical (add cores) |
| Overhead | MPI latency | HTTP serialization |

## Algorithm: Fox Block Multiplication

The Fox algorithm divides matrices into q×q blocks and computes in q phases:

- **Grid**: q×q processor grid
- **Threads**: q² concurrent threads
- **Phases**: q synchronization points
- **Requirement**: n % q == 0

Example with n=4, q=2:
- 4 threads (2×2 grid)
- 2 phases
- Each thread processes 2×2 submatrices

## Project Structure

```
src/main/java/ua/kpi/lab8/
├── Application.java           # Spring Boot main
├── controller/
│   └── MatrixController.java  # REST endpoints
├── service/
│   └── MatrixService.java     # Business logic
├── algorithm/
│   ├── FoxParallelMultiplier.java
│   ├── MatrixMultiplier.java
│   └── ExecutorUtils.java
├── model/
│   ├── ServerMultiplyRequest.java
│   ├── ClientMultiplyRequest.java
│   └── MultiplyResponse.java
└── benchmark/
    └── BenchmarkRunner.java   # Standalone benchmarks
```
