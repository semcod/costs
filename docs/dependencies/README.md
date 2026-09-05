# Aktualizacje zależności costs

Dokumentacja utrzymywana w `semcod/costs`, dotycząca wydań costs i aktualizacji jego konsumentów. Właścicielem wykonawcy aktualizacji jest `semcod/goal`.

- [Raport wdrożenia z 2026-09-05](rollout-2026-09-05.md) — wykonane zmiany, wyniki kontroli i pozostały zakres.
- [Dowody w JSON](rollout-2026-09-05.json) — wersje, SHA256 publikacji, commity, PR-y i uruchomienia CI.
- [Druga grupa aktualizacji](rollout-batch-2-2026-09-05.md) — sześć kolejnych wdrożeń i imgl oczekujące na przegląd.
- [Dowody drugiej grupy](rollout-batch-2-2026-09-05.json).
- [Trzecia grupa aktualizacji](rollout-batch-3-2026-09-05.md) — sześć wdrożeń, poprawione metryki nxdo i zgodność planfile.
- [Dowody trzeciej grupy](rollout-batch-3-2026-09-05.json) — także pozostali kandydaci z historycznego audytu.
- [Instrukcja wykonawcy Goal](https://github.com/semcod/goal/blob/84f18540d14c24cc8ff5b7f202d2874344779ecc/docs/internal-dependencies.md).

Kolejne raporty zapisujemy w tym katalogu i dodajemy do tego indeksu. Instrukcje konkretnego konsumenta należą do jego `docs/`. Raport jest wersjonowany wraz z repozytorium i nie zależy od prywatnej ścieżki na komputerze autora. Surowe logi, środowiska testowe i pliki tymczasowe nie zastępują dokumentacji wynikowej.

Przyjęto zasadę dokumentacji należącej do repozytorium z [wellmanifest/docs](https://github.com/wellmanifest/docs/blob/f64de5806577769672ebc1730d2e144b4c7671ec/README.md). Ten pakiet w odczytanej rewizji jest zalążkiem standardu; nie udostępnia osobnego schematu walidacji raportów. Schemat JSON obok raportu jest lokalnym formatem costs, a nie certyfikatem zgodności wellmanifest.
