# Трекер джерел для курсової роботи

Тема: `Алгоритм бітонічного сортування та його паралельна реалізація Python`

## Принцип відбору

У цьому файлі фіксуються лише зовнішні джерела, які потенційно можна включати до списку використаних джерел:
- книги;
- статті;
- навчальні публікації;
- лекційні матеріали;
- офіційна документація.

Не включаємо сюди:
- методичні вимоги;
- власний код;
- тести;
- внутрішні нотатки;
- результати власних експериментів.

## Основні джерела

### A01. Justin R. Smith. The Design and Analysis of Parallel Algorithms

- Статус: `використати`
- Тип: книга
- Джерело: `course-work/docs/materials/The_Design_and_Analysis_of_Parallel_Algo.pdf`
- Навіщо: загальна мотивація паралельних алгоритмів, незалежні обчислення, обчислювальні мережі.
- Де може знадобитись: вступ, теоретична частина.

### A02. Kenneth E. Batcher. Sorting networks and their applications

- Статус: `використати`
- Тип: стаття / першоджерело
- URL: `https://www.cs.kent.edu/~batcher/sort.pdf`
- Навіщо: класичне першоджерело для bitonic sort і sorting networks.
- Де може знадобитись: розділ 1, псевдокод, історія алгоритму.

### A03. Bitonic sort overview

- Статус: `використати`
- Тип: навчальні матеріали
- URL: `https://people.cs.rutgers.edu/~venugopa/parallel_summer2012/bitonic_overview.html`
- Навіщо: наочне пояснення побудови бітонічної послідовності та етапів злиття.
- Де може знадобитись: розділ 1.

### A04. Lecture notes on bitonic sort

- Статус: `використати`
- Тип: лекційні матеріали
- URL: `https://cse.buffalo.edu/faculty/miller/Courses/CSE633/Mullapudi-Spring-2014-CSE633.pdf`
- Навіщо: короткий і зручний опис алгоритму та його паралельної природи.
- Де може знадобитись: вступ, розділ 1.

### A05. Donald E. Knuth. The Art of Computer Programming, Volume 3: Sorting and Searching

- Статус: `використати`
- Тип: книга
- Джерело: `course-work/docs/materials/Art of Computer Programming - Volume 3 (Sorting & Searching)-231-260.pdf`
- Навіщо: теоретичний опис sorting networks, comparator modules та властивостей oblivious sorting.
- Де може знадобитись: розділ 1.

### A06. CLRS / розділ про sorting networks

- Статус: `перевірити`
- Тип: підручник
- URL: `https://iitdh.ac.in/~konjengbam.anand/courses/daa/CLRS4e2022.pdf`
- Навіщо: теорія сортувальних мереж.
- Коментар: перед використанням треба зафіксувати точні сторінки.

### A07. NIST Dictionary of Algorithms and Data Structures

- Статус: `перевірити`
- Тип: довідкове джерело
- URL: `https://xlinux.nist.gov/dads/HTML/bitonicSort.html`
- Навіщо: коротке формальне визначення.
- Коментар: краще використовувати як допоміжне, не як основне.

### A08. Utah parallel algorithms lecture slides

- Статус: `перевірити`
- Тип: лекційні матеріали
- URL: `https://users.cs.utah.edu/~hari/teaching/paralg/slides/lec06.html#/3/18`
- Навіщо: додаткове пояснення паралельних алгоритмів сортування.

### A09. Georgia Tech lecture on bitonic sort

- Статус: `використати`
- Тип: лекційні матеріали
- Джерело: `course-work/docs/materials/lec11-bitonicsort.pdf`
- Навіщо: сучасніші навчальні слайди по bitonic sort, bitonic split і sorting network.
- Де може знадобитись: розділ 1, особливо для рисунків і наочного пояснення.

### A10. Steve Dower. Bitonic Sort

- Статус: `перевірити`
- Тип: технічна публікація
- URL: `https://stevedower.id.au/papers/bitonic_sort_2012.pdf`
- Навіщо: може бути корисним для опису реалізаційних деталей.
- Коментар: спершу треба оцінити академічність і якість.

### A11. arXiv material on bitonic sort

- Статус: `використати обережно`
- Тип: наукова публікація
- Джерело: `course-work/docs/materials/1506.01446v1.pdf`
- Навіщо: приклад практичної CUDA-реалізації bitonic sort, обговорення kernel launches, shared memory і block-level оптимізацій.
- Коментар: джерело корисне для огляду відомих паралельних реалізацій, але не варто робити його основним теоретичним джерелом, оскільки воно орієнтоване на GPU і має неідеальну базу посилань.

### A12. Grama et al. Introduction to Parallel Computing (Algorithm 9.1)

- Статус: `використати`
- Тип: книга (фрагмент із розділом/алгоритмом)
- Джерело: `course-work/docs/materials/Introduction to Parallel Computing, Second Edition-Ananth Grama, Anshul Gupta, George Karypis, Vipin Kumar-391-405.pdf`
- Навіщо: псевдокод паралельної формалізації bitonic sort на гіперкубі (Algorithm 9.1), а також оцінка кількості кроків та часу виконання `O(log^2 n)`.
- Де може знадобитись: підрозділ `4.1`, опис логіки паралельних compare-exchange операцій і асимптотики.

## Офіційна документація, яку ще варто добрати

### D01. Python `multiprocessing`

- Статус: `використати`
- Тип: офіційна документація
- URL: `https://docs.python.org/3/library/multiprocessing.html`
- Навіщо: для розділу 3 і розділу 4.

### D02. Python `multiprocessing.shared_memory`

- Статус: `використати`
- Тип: офіційна документація
- URL: `https://docs.python.org/3/library/multiprocessing.shared_memory.html`
- Навіщо: для опису поточної технічної реалізації.

### D03. Python `threading`

- Статус: `використати`
- Тип: офіційна документація
- URL: `https://docs.python.org/3/library/threading.html`
- Навіщо: для короткого порівняння з процесною моделлю та пояснення обмежень для CPU-bound задач.

### D04. Python `concurrent.futures`

- Статус: `використати`
- Тип: офіційна документація
- URL: `https://docs.python.org/3/library/concurrent.futures.html`
- Навіщо: для огляду альтернативного високорівневого інтерфейсу організації паралельних задач у Python.

## Не використовувати у фінальному списку літератури

### X01. YouTube

- URL: `https://www.youtube.com/watch?v=uEfieI0MumY`
- Причина: неакадемічне джерело.

### X02. Javatpoint

- URL: `https://web.archive.org/web/20241122030200/https://www.javatpoint.com/bitonic-sort`
- Причина: популярний вторинний ресурс.

### X03. GeeksForGeeks

- URL-и:
  - `https://www.geeksforgeeks.org/python/python-program-for-bitonic-sort/`
  - `https://www.geeksforgeeks.org/dsa/bitonic-sorting-network-using-parallel-computing/`
- Причина: вторинні популярні матеріали.

### X04. Stack Overflow

- URL-и:
  - `https://stackoverflow.com/questions/79143120/parallel-bitonic-sort-implementation-speedup`
  - `https://stackoverflow.com/questions/47213007/python-3-6-bitonic-sort-with-multiprocessing-library-and-multiple-processes`
- Причина: корисно для відлагодження, але не для бібліографії.

### X05. Fandom / wiki-подібні ресурси

- URL-и:
  - `https://neo-sorting-algorithms.fandom.com/wiki/Bitonic_sort`
  - `https://sortingalgos.miraheze.org/wiki/Bitonic_Sort`
- Причина: ненадійні вторинні джерела.

### X06. Неофіційні технічні сторінки

- URL-и:
  - `https://hwlang.de/algorithmen/sortieren/bitonic/bitonicen.htm`
  - `https://forejune.co/cuda/sort/sort.html`
- Причина: можна читати для себе, але не варто додавати в академічний список джерел без окремої перевірки.

## Де вже використано джерела

- `course-work/docs/sections/01-vstup.md` зараз спирається на `A01-A04`.

