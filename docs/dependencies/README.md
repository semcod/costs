# Archiwum aktualizacji zależności costs

Historyczne dowody wydań costs i aktualizacji konsumentów pozostają w tym repozytorium. Kanoniczny [raport przekrojowy](https://github.com/subactor/docs/blob/main/architecture/analysis/internal-dependencies.md) należy do `subactor/docs`; ten indeks prowadzi do jego bieżącej wersji. Dokładne rewizje i dowody znajdują się w raporcie, a starsze obserwacje zachowuje [historia Git dokumentu](https://github.com/subactor/docs/commits/main/architecture/analysis/internal-dependencies.md). Właścicielem wykonawcy aktualizacji jest `semcod/goal`.

- [Raport wdrożenia z 2026-09-05](rollout-2026-09-05.md) — wykonane zmiany, wyniki kontroli i pozostały zakres.
- [Dowody w JSON](rollout-2026-09-05.json) — wersje, SHA256 publikacji, commity, PR-y i uruchomienia CI.
- [Druga grupa aktualizacji](rollout-batch-2-2026-09-05.md) — sześć kolejnych wdrożeń i imgl oczekujące na przegląd.
- [Dowody drugiej grupy](rollout-batch-2-2026-09-05.json).
- [Trzecia grupa aktualizacji](rollout-batch-3-2026-09-05.md) — sześć wdrożeń, poprawione metryki nxdo i zgodność planfile.
- [Dowody trzeciej grupy](rollout-batch-3-2026-09-05.json) — także pozostali kandydaci z historycznego audytu.
- [Instrukcja wykonawcy Goal](https://github.com/semcod/goal/blob/84f18540d14c24cc8ff5b7f202d2874344779ecc/docs/internal-dependencies.md).

Nowe ustalenia przekrojowe dopisujemy przez zwiększenie wersji kanonicznego dokumentu `subactor/docs:architecture/analysis/internal-dependencies.md`. Powyższe raporty są historycznymi zapisami; nie tworzymy kolejnych kopii bieżącego raportu w costs.

Lokalne informacje costs należą do `docs/information/`, analizy do `docs/analysis/`, plany do `docs/refactoring/`, a decyzje do `docs/decisions/`, z indeksem w `docs/README.md`. Obowiązują metadane i sekcje [wellmanifest/docs 0.1.1](https://github.com/wellmanifest/docs/blob/ebe7501063ef4f3e63ded610c2d3183010ca636e/docs/standard/POLICY.md). Starsze raporty zachowują swoje formaty i odniesienia jako historię. Sam odnośnik do standardu nie dowodzi adopcji jego checkera ani egzekwowania w CI.

Surowe logi, środowiska testowe i kopie odzyskiwania pozostają w prywatnym magazynie roboczym; nie zastępują wersjonowanej dokumentacji wynikowej.
