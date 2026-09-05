# Aktualizacje zależności — druga grupa, 2026-09-05

Właściciel raportu: `semcod/costs`. Kontynuacja [pierwszego wdrożenia](rollout-2026-09-05.md). Raport opisuje zaobserwowany stan; nie gwarantuje aktualności wszystkich repozytoriów w przyszłości.

## Wynik

Sześć kolejnych repozytoriów ma scalone aktualizacje, codzienny Dependabot i kontrolę najwyższych stabilnych wersji z katalogu. Potwierdzono testy na main, audyt z main oraz pierwsze wykonania Dependabota. Razem z poprzednią grupą daje to dziesięciu potwierdzonych konsumentów; Goal ma własny audyt.

| Repo / PR | Publikacja | Python testów | Lokalne testy: przeszły / pominięte, na każdej wersji |
|---|---|---|---|
| [semcod/clickmd](https://github.com/semcod/clickmd/pull/1) | scalono; [audyt main](https://github.com/semcod/clickmd/actions/runs/33989821871) | 3.10 / 3.13 | 66 / 3 |
| [semcod/pfix](https://github.com/semcod/pfix/pull/1) | scalono; [audyt main](https://github.com/semcod/pfix/actions/runs/33989823335) | 3.10 / 3.13 | 180 / 1 |
| [semcod/code2llm](https://github.com/semcod/code2llm/pull/1) | scalono; [audyt main](https://github.com/semcod/code2llm/actions/runs/33989824619) | 3.10 / 3.13 | 298 / 0 |
| [semcod/mdflow](https://github.com/semcod/mdflow/pull/1) | scalono; [audyt main](https://github.com/semcod/mdflow/actions/runs/33989826053) | 3.11 / 3.13 | 2 / 0 |
| [semcod/giton](https://github.com/semcod/giton/pull/2) | scalono; [audyt main](https://github.com/semcod/giton/actions/runs/33989827539) | 3.10 / 3.13 | 49 / 0 |
| [autogrammar/code2schema](https://github.com/autogrammar/code2schema/pull/1) | scalono; [audyt main](https://github.com/autogrammar/code2schema/actions/runs/33989828760) | 3.10 / 3.13 | kod 0 |
| [autogrammar/imgl](https://github.com/autogrammar/imgl/pull/2) | PR otwarty; wymagany niezależny przegląd | 3.10 / 3.13 | 163 / 11 |

Wszystkie siedem projektów przeszło lokalne testy, `uv lock --check`, audyt wersji oraz budowę wheel i sdist. [Dowód JSON](rollout-batch-2-2026-09-05.json) zawiera commity, wyniki i odnośniki do CI. Wersje docelowe w katalogu: costs 0.2.0, Goal 2.2.0, pfix 0.1.79, clickmd 1.1.15, code2llm 0.5.176; repo sprawdza tylko faktycznie użyte pakiety i wyłącza własny pakiet editable.

## Zmiany

Goal przeniesiono do grupy `automation` wymagającej Pythona >=3.12. Zachowano dotychczasowy minimalny Python aplikacji. W clickmd i mdflow usunięto również nieużywaną deklarację Goal z zależności wykonawczych. Aktualizacje rozwiązano w uv.lock, a CI instaluje zależności z tego pliku.

W clickmd poprawiono składnię podświetlania JSON, która nie parsowała się na Pythonie 3.10. W imgl zastąpiono `datetime.UTC` przez `timezone.utc`, udostępniono pytest kod lokalnego adaptera MCP i dodano Tesseract z danymi eng/pol do CI testującego OCR. W giton uwzględniono katalog źródeł przykładowego projektu w zbieraniu testów. Zestawy testów nie zostały zawężone w celu ukrycia błędów.

Każde repo ma własny `docs/dependencies.md`, wskazany w README. Zasada własności dokumentacji pochodzi z [wellmanifest/docs](https://github.com/wellmanifest/docs/blob/f64de5806577769672ebc1730d2e144b4c7671ec/README.md). Ten zalążek standardu nie dostarcza osobnego schematu walidacji raportów; JSON jest lokalnym formatem costs. Pliki wynikowe są wersjonowane w repo, a logi i środowiska robocze są materiałem tymczasowym.

## Pozostałe warunki i dalsze poprawki

- **imgl:** [PR #2](https://github.com/autogrammar/imgl/pull/2) wymaga niezależnego zatwierdzenia ostatniego commita zgodnie z [regułą main-supervised-autonomy](https://github.com/autogrammar/imgl/rules/21952608). CI wystawia wymagany check `test`, który przechodzi tylko po sukcesie obu wersji Pythona. [Testy i check test](https://github.com/autogrammar/imgl/actions/runs/33989900427) oraz [audyt wersji](https://github.com/autogrammar/imgl/actions/runs/33989900424) przeszły na ostatnim commicie. Dozwolona metoda scalenia to merge commit. Harmonogramy zaczną działać po scaleniu.
- **glon i pozostałe repo z governance:** potrzebują aktualizacji przez proces ticketów i wymagane zatwierdzenia. Nie uruchomiono w nich tego prostego wariantu migracji.
- **Pełny katalog i instalacje:** dotychczasowy historyczny audyt obejmował 187 repo, a konfiguracje tutaj dotyczą pięciu jawnie wskazanych pakietów. Pozostają inni konsumenci, lokalne/Git źródła, pozostałe pakiety wewnętrzne oraz synchronizacja faktycznie używanych środowisk.
- **Szybsze aktualizacje:** kolejnym krokiem jest wspólny mechanizm wyzwalany po publikacji pakietu, który przygotuje aktualizację u konsumentów. Samo `>=` nie odświeża uv.lock, a codzienny PR nie jest dowodem scalenia ani instalacji. Rozszerzanie zakresu wersji nadal wymaga testów zgodności.
- **code2schema:** istniejący, niezależny [workflow synchronizacji metadanych organizacji](https://github.com/autogrammar/code2schema/actions/runs/33989761935) nie otrzymuje tokenu uwierzytelniającego. Testy i audyt zależności przeszły; konfiguracja dostępu do synchronizacji wymaga osobnej naprawy.
- **mdflow:** lokalny hook pre-commit sprawdza tekst ASCII `| error `, choć prefact wypisuje tabelę ze znakami Unicode. W obserwowanym wykonaniu zaakceptował raport zawierający pozycję `error`. Warto zastąpić parsowanie wyglądu tabeli wynikiem maszynowym narzędzia. Lint, formatowanie i testy tej zmiany przeszły.

Audyt imgl wymagał jednego ponowienia po zerwaniu połączenia z PyPI (`Connection reset by peer`); drugie wykonanie przeszło. W wykonawcy Goal warto dodać ograniczone ponawianie przejściowych błędów sieci, zachowując błąd końcowy i dowód próby.
