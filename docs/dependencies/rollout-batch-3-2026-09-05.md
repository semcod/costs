# Aktualizacje zależności — trzecia grupa, 2026-09-05

Właściciel raportu: `semcod/costs`. Kontynuacja [drugiej grupy](rollout-batch-2-2026-09-05.md). Sześć kolejnych repozytoriów ma scalone aktualizacje i sprawdzone działanie codziennych kontroli. Łącznie w trzech grupach potwierdzono wdrożenie u 16 konsumentów; Goal ma dodatkowo własny audyt.

## Wdrożenie i dowody

| Repo / scalony PR | Lokalne testy: przeszły / pominięte, na każdej wersji | Kontrole z main |
|---|---|---|
| [semcod/docval](https://github.com/semcod/docval/pull/1) | 43 / 0 | [audyt](https://github.com/semcod/docval/actions/runs/33991333674), [testy](https://github.com/semcod/docval/actions/runs/33991333322), [Dependabot](https://github.com/semcod/docval/actions/runs/33991338863) |
| [semcod/fixop](https://github.com/semcod/fixop/pull/1) | 102 / 0 | [audyt](https://github.com/semcod/fixop/actions/runs/33991338021), [testy](https://github.com/semcod/fixop/actions/runs/33991337489), [Dependabot](https://github.com/semcod/fixop/actions/runs/33991343877) |
| [semcod/nxdo](https://github.com/semcod/nxdo/pull/4) | 138 / 0 | [audyt](https://github.com/semcod/nxdo/actions/runs/33991896541), [testy](https://github.com/semcod/nxdo/actions/runs/33991895830), [Dependabot](https://github.com/semcod/nxdo/actions/runs/33991899520) |
| [semcod/planfile](https://github.com/semcod/planfile/pull/54) | 440 / 6 | [audyt](https://github.com/semcod/planfile/actions/runs/33991343224), [testy](https://github.com/semcod/planfile/actions/runs/33991342903), [Dependabot](https://github.com/semcod/planfile/actions/runs/33991346650) |
| [autogrammar/op3](https://github.com/autogrammar/op3/pull/1) | 132 / 0 | [audyt](https://github.com/autogrammar/op3/actions/runs/33991347860), [testy](https://github.com/autogrammar/op3/actions/runs/33991347483), [Dependabot](https://github.com/autogrammar/op3/actions/runs/33991353567) |
| [autogrammar/toonic](https://github.com/autogrammar/toonic/pull/1) | 454 / 0 | [audyt](https://github.com/autogrammar/toonic/actions/runs/33991352828), [testy](https://github.com/autogrammar/toonic/actions/runs/33991351958), [Dependabot](https://github.com/autogrammar/toonic/actions/runs/33991357561) |

Lokalne testy obejmują Python 3.10 i 3.13. CI nxdo sprawdza dodatkowo 3.11 i 3.12 oraz pokrycie, typy, lint i przykłady. Każdy projekt przeszedł budowę wheel/sdist, weryfikację uv.lock i audyt najwyższych stabilnych wersji pakietów z jawnego katalogu. Pobrane artefakty audytu z main potwierdzają `fresh: true`; ich sumy manifestu i lockfile porównano z opublikowanymi zmianami. [Dowody JSON](rollout-batch-3-2026-09-05.json) zawierają commity, PR-y, wyniki i konkretne uruchomienia.

Wersje docelowe: costs 0.2.0, Goal 2.2.0, pfix 0.1.79, clickmd 1.1.15 i code2llm 0.5.176. Kontrola uwzględnia te pakiety z katalogu, które faktycznie występują w lockfile. Stan aktualności dotyczy czasu pomiaru, nie dowolnej przyszłej instalacji.

## Poprawa liczenia i testów nxdo

W liczeniu commitów naprawczych jeden commit mógł być liczony wielokrotnie, jeśli pasował do kilku słów, np. „fix”, „bug” i „repair”. Zapytanie Git łączy teraz warunki i zlicza unikalne identyfikatory. Liczba zapytań do Git dla tego licznika spadła z siedmiu do jednego na plik. Test na rzeczywistej tymczasowej historii potwierdza pojedyncze naliczenie i liczbę wywołań.

Dodano testy historii zmian, autorów i powiązań plików, niedostępnego Git, opcjonalnej integracji Koru, wzbogacania promptu oraz granic trybu `auto --dry-run` i zapisu ticketów. Zastąpiono pusty test rzeczywistą weryfikacją. Pokrycie wzrosło z 71,21% w pierwszym przebiegu CI do 95,98% w lokalnych pomiarach; wymagany próg 95% pozostał bez zmian. Przechodzi 138 testów.

Dotychczasowy CI nxdo korzystał z nieograniczonej instalacji pip i pobierał Ruff 0.16.6, podczas gdy uv.lock zawierał 0.15.17. Powodowało to różne reguły lintowania lokalnie i w CI. Cały istniejący workflow korzysta teraz z uv.lock, zachowując wszystkie kontrole i cztery wersje Pythona. `pytest-cov` jest zadeklarowany w zależnościach dev.

## Zgodność Pythona i własność dokumentacji

We wszystkich sześciu repo Goal przeniesiono do grupy `automation` wymagającej Pythona >=3.12. Zachowano Python >=3.10 dla aplikacji. W docval i fixop usunięto też nieużywaną zależność wykonawczą od Goal, po sprawdzeniu kodu aplikacji.

W planfile poprawiono importy `datetime.UTC` w aplikacji i testach na `timezone.utc`, przywracając obsługę deklarowanego Pythona 3.10. Testy obejmują daty UTC i archiwizację ticketów. Adresy Homepage/Repository w źródłowych metadanych wskazują teraz semcod/planfile.

Każdy konsument ma instrukcję `docs/dependencies.md` wskazaną w README. Raport zbiorczy i dowody należą do costs, zgodnie z zasadą własności dokumentacji w [wellmanifest/docs](https://github.com/wellmanifest/docs/blob/f64de5806577769672ebc1730d2e144b4c7671ec/README.md). W tej rewizji pakiet jest zalążkiem standardu i nie udostępnia osobnego schematu raportów; użyty JSON jest lokalnym formatem costs.

## Dalsze prace

- **imgl:** [PR #2](https://github.com/autogrammar/imgl/pull/2) nadal wymaga niezależnego przeglądu ostatniego commita zgodnie z regułami repo. Zielone kontrole opisano w poprzednim raporcie; nie zaliczono go do scalonych wdrożeń.
- **planfile:** W odczytanych metadanych PyPI ostatnim wydaniem było [0.1.123](https://pypi.org/project/planfile/0.1.123/), a repo deklaruje 0.1.125. Zmiany w repo nie publikują automatycznie nowego pakietu ani poprawionych metadanych PyPI. Potrzebne jest osobne wydanie i późniejsza aktualizacja jego odbiorców, m.in. nxdo.
- **op3 i toonic:** istniejąca synchronizacja metadanych organizacji nie otrzymuje tokenu uwierzytelniającego. [Błąd op3](https://github.com/autogrammar/op3/actions/runs/33991347429) i [błąd toonic](https://github.com/autogrammar/toonic/actions/runs/33991351954) dotyczą tego osobnego workflow; audyty zależności i testy aplikacji przeszły.
- **toonic:** testy zgłaszają ostrzeżenie: `Logging.async_success_handler` nie został obsłużony przez `await`. Warto uporządkować zamykanie zadań asynchronicznych.
- **Pozostały ekosystem:** katalog obejmuje pięć wskazanych pakietów, nie wszystkie zależności wewnętrzne. Pozostają inni konsumenci, lokalne/Git źródła, repo z governance, wyzwalanie aktualizacji po wydaniu oraz faktyczna synchronizacja środowisk. W JSON zapisano pozostałych kandydatów z historycznego audytu, po odjęciu wykonanych wdrożeń; nie jest to świeża inwentaryzacja zdalnych repo.

Codzienny aktualizator przygotowuje PR. Deklaracja `>=` nie odświeża uv.lock, a otwarty PR nie jest dowodem zatwierdzenia, scalenia ani instalacji. Obowiązują testy i reguły poszczególnych repozytoriów.
