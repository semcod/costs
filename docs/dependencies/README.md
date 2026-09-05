# Archiwum aktualizacji zależności costs

Historyczne dowody wydań costs i aktualizacji konsumentów pozostają w tym repozytorium. Kanoniczny [raport przekrojowy](https://github.com/subactor/docs/blob/3391236d3cc0732a11f1e87492f2fb053d228dcf/architecture/analysis/internal-dependencies.md) należy do `subactor/docs`; jego pierwsza wersja jest w [PR #26](https://github.com/subactor/docs/pull/26), jeszcze niescalona. Właścicielem wykonawcy aktualizacji jest `semcod/goal`.

- [Raport wdrożenia z 2026-09-05](rollout-2026-09-05.md) — wykonane zmiany, wyniki kontroli i pozostały zakres.
- [Dowody w JSON](rollout-2026-09-05.json) — wersje, SHA256 publikacji, commity, PR-y i uruchomienia CI.
- [Druga grupa aktualizacji](rollout-batch-2-2026-09-05.md) — sześć kolejnych wdrożeń i imgl oczekujące na przegląd.
- [Dowody drugiej grupy](rollout-batch-2-2026-09-05.json).
- [Trzecia grupa aktualizacji](rollout-batch-3-2026-09-05.md) — sześć wdrożeń, poprawione metryki nxdo i zgodność planfile.
- [Dowody trzeciej grupy](rollout-batch-3-2026-09-05.json) — także pozostali kandydaci z historycznego audytu.
- [Instrukcja wykonawcy Goal](https://github.com/semcod/goal/blob/84f18540d14c24cc8ff5b7f202d2874344779ecc/docs/internal-dependencies.md).

Nowe ustalenia przekrojowe dopisujemy przez zwiększenie wersji kanonicznego dokumentu `subactor/docs:architecture/analysis/internal-dependencies.md`. Powyższe raporty są historycznymi zapisami; nie tworzymy kolejnych kopii bieżącego raportu w costs.

Lokalne informacje costs należą do `docs/information/`, analizy do `docs/analysis/`, plany do `docs/refactoring/`, a decyzje do `docs/decisions/`, z indeksem w `docs/README.md`. Obowiązują metadane i sekcje [wellmanifest/docs 0.1.0](https://github.com/wellmanifest/docs/blob/fdb0fcaa7c606dc2503cabb71eff64d5f86ee659/docs/standard/POLICY.md). Starsze raporty zachowują swoje formaty i odniesienia jako historię. Sam odnośnik do standardu nie dowodzi adopcji jego checkera ani egzekwowania w CI.

Surowe logi, środowiska testowe i kopie odzyskiwania pozostają w prywatnym magazynie roboczym; nie zastępują wersjonowanej dokumentacji wynikowej.
