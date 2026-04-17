# База знань: практикум 7 (MPI, колективний обмін)

Короткий конспект для звіту. **Повне джерело** — [2.5 МРІ-методи колективного обміну.pdf](materials/2.5%20МРІ-методи%20колективного%20обміну.pdf) у `lab7/docs/materials/`. Документація стандарту: [mpi-forum.org/docs](https://www.mpi-forum.org/docs/).

---

## Класи колективів

- **Синхронізація:** `MPI_Barrier` — усі процеси в комунікаторі доходять до точки бар’єра перед продовженням.
- **Один-до-багатьох:** `MPI_Bcast` (одна копія даних усім), `MPI_Scatter` / `MPI_Scatterv` (розбиття масиву з root по процесах; `Scatterv` — змінні розміри блоків і зміщення `displs`).
- **Багато-до-одного:** `MPI_Gather` / `MPI_Gatherv`, `MPI_Reduce` / `MPI_Allreduce` (останні — для редукцій з операцією).
- **Багато-до-багатьох:** `MPI_Allgather` / `MPI_Allgatherv`, `MPI_Alltoall` / `MPI_Alltoallv`.

Для **нерівномірного** розбиття рядків матриці між процесами у множенні $C = AB$ зручні **`Scatterv`** / **`Gatherv`** / **`Allgatherv`** з масивами `sendcounts` і `displs` (у елементах буфера).

---

## Зв’язок із реалізацією lab7

Код: пакет `matrix_multiplication` у [`lab7/project/src/matrix_multiplication/`](../../project/src/matrix_multiplication/) (реалізації в [`implementations/`](../../project/src/matrix_multiplication/implementations/)).

| Патерн у звіті | Примітиви mpi4py у проєкті |
|----------------|---------------------------|
| один-до-одного | `Comm.Send` / `Recv` (`p2p`) |
| колективний основний (п. 2) | `Scatterv`, `Bcast`, `Gatherv` (`collective_sbg`) |
| P2P + збір на root | роздача `Send`/`Recv`, збір `Gatherv` (`p2p_gatherv`) |
| багато-до-багатьох (результат усім) | `Scatterv`, `Bcast`, `Allgatherv` (`allgatherv`) |

Час вимірюється на інтервалі від початку комунікації роздачі до завершення збору результату (аналогічно до опису для практикуму 6).
