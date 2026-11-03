# Prezentacja: GitHub Actions, Semgrep i review AI

Instrukcja dla prowadzącego. Czas prezentacji: około 15–20 minut,
plus czas oczekiwania na workflow. Konfigurację i próbę wykonaj wcześniej.

## 1. Co pokazujemy

Historia demonstracji:

1. Programista wprowadza SQL injection i otwiera pull request.
2. GitHub uruchamia automatyczne kontrole na tymczasowych maszynach Ubuntu.
3. Semgrep wykrywa niebezpieczny wzorzec.
4. AI publikuje komentarz z wyjaśnieniem i propozycją poprawki.
5. Programista poprawia kod i wysyła kolejny commit.
6. Kontrole uruchamiają się ponownie, a komentarz AI zostaje zaktualizowany.

Zdanie otwierające prezentację:

> „Pokażę, jak do zwykłego pull requestu dodać automatyczną kontrolę
> bezpieczeństwa i review AI. Semgrep sprawdza reguły, a AI pomaga
> zrozumieć zmianę. Decyzję o scaleniu nadal podejmuje człowiek.”

## 2. Jak działa to repozytorium

| Plik lub katalog | Rola w demonstracji |
| --- | --- |
| `.github/workflows/demo.yml` | Instalacja i uruchomienie Semgrep oraz Conftest |
| `.github/workflows/ai-review.yml` | Uruchomienie doradczego review dla PR-a |
| `ai_review.py` | Pobranie diffu, wywołanie OpenAI, aktualizacja komentarza |
| `app/UserController.java` | Kod roboczy, który zmieniamy w PR-ze |
| `app_vuln/UserController.java` | Gotowy przykład SQL injection |
| `app_fixed/UserController.java` | Poprawka z `PreparedStatement` |
| `rules/java-sqli-demo.yml` | Lokalna reguła Semgrep dla przykładu |
| `infra/deployment.yaml` | Manifest sprawdzany przez Conftest |
| `policies/deployment.rego` | Wymagane limity CPU i pamięci |

### Co faktycznie dzieje się na maszynach GitHuba

Każdy z dwóch jobów otrzymuje własne środowisko. Nie zakładamy, że
współdzielą pliki ani zainstalowane narzędzia.

**Job bezpieczeństwa:** pobiera kod, przygotowuje Pythona, instaluje
Semgrep, skanuje pliki, instaluje Conftest i sprawdza manifest.
Przy błędzie Semgrep kolejne kroki zwykle są pomijane.

**Job review AI:** pobiera zaufany skrypt z commita bazowego PR-a,
przygotowuje Pythona i wykonuje `python3 ai_review.py`. Skrypt pobiera
diff przez API GitHuba, wysyła go do API OpenAI i publikuje komentarz.
Model działa po stronie OpenAI, a nie na runnerze. Kod z PR-a nie jest
wykonywany przez ten job. Oba joby mogą działać równolegle.

Skrypty `pipeline_fail.sh` i `pipeline_ai_fix.sh` służą do osobnej,
lokalnej demonstracji. Obecne workflow nie wywołują ich automatycznie.
Review AI nie uruchamia automatycznej naprawy kodu.

## 3. Przygotowanie przed prezentacją

### 3.1. Repozytorium i gałąź bazowa

Potrzebujesz repozytorium GitHub, uprawnień do wysyłania zmian i dodawania
sekretów, lokalnego Gita oraz dostępu do API OpenAI dla wybranego modelu.
Semgrep, Conftest i pakiet `openai` nie muszą być zainstalowane na laptopie
do prezentacji wykonywanej wyłącznie w Actions.

Umieść **zawartość** katalogu `demo-secure-sdlc` w głównym katalogu
repozytorium GitHub. Struktura musi wyglądać tak:

```text
repozytorium/
  .github/workflows/demo.yml
  .github/workflows/ai-review.yml
  ai_review.py
  app/
  app_fixed/
  app_vuln/
  infra/
  policies/
  rules/
```

Jeśli `.github` pozostanie w podkatalogu `demo-secure-sdlc`, GitHub
nie odkryje tych workflow jako workflow repozytorium.

Dalsze polecenia wykonuj w katalogu głównym sklonowanego repozytorium.
Zakładamy gałąź `main` i remote `origin`; dostosuj nazwy, jeśli są inne.
Najpierw sprawdź `git status` i zachowaj własne niezacommitowane zmiany.
Nie dodawaj do repozytorium `.venv/`, plików `.env` ani prawdziwych sekretów.

Na gałęzi bazowej przygotuj bezpieczny punkt startowy:

```bash
git switch main
git pull --ff-only origin main
cp app_fixed/UserController.java app/UserController.java
```

Przygotowane workflow, skrypt review, reguły i bezpieczny plik aplikacji
muszą być zacommitowane i scalone do `main` **przed otwarciem PR-a demo**.
To ważne: reviewer uruchamia skrypt z bazy PR-a. Samo dodanie skryptu
w demonstracyjnym PR-ze nie wystarcza.

### 3.2. Sekret i model

W repozytorium na GitHubie:

1. Otwórz **Settings → Secrets and variables → Actions**.
2. W **Secrets** wybierz **New repository secret**.
3. Nazwa: `OPENAI_API_KEY`. Wartość: nowy klucz API.
4. Opcjonalnie w **Variables** dodaj `OPENAI_REVIEW_MODEL`.
   Bez tej zmiennej skrypt używa `gpt-4.1-mini`.

Nie pokazuj wartości klucza na ekranie. Wcześniej zapisany w kodzie
prawdziwy klucz trzeba unieważnić; samo usunięcie z aktualnego pliku
nie usuwa go z historii. Nie wypychaj historii zawierającej aktywne sekrety.

`GITHUB_TOKEN` jest dostarczany automatycznie. Nie twórz dla tego demo
osobnego personal access tokena. Workflow deklaruje `contents: read`
i `pull-requests: write`; polityka organizacji musi je dopuszczać.
W **Settings → Actions → General** sprawdź, czy Actions i użyte akcje
`actions/checkout` oraz `actions/setup-python` są dozwolone.
Nie jest potrzebna opcja pozwalająca Actions tworzyć i zatwierdzać PR-y:
nasz skrypt dodaje zwykły komentarz.

Review działa dla gotowego PR-a z gałęzi **tego samego repozytorium**.
PR-y z forków, drafty i uruchomienia przez Dependabot są pomijane.

### 3.3. Przygotowanie czerwonej kontroli Semgrep

**Stan obecny:** konfiguracja opisana poniżej jest już zastosowana w `demo.yml`.
Semgrep reaguje na PR-y i pushe do `main`, używa lokalnej reguły oraz `--error`.
Instalacja jest przypięta do Semgrep 1.183.0 i Conftest 0.71.1;
adres archiwum Conftest zawiera numer wersji. Poniższe fragmenty służą
weryfikacji ustawień, nie wymagają ponownego edytowania pliku.

Sekcja zdarzeń:

```yaml
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
```

Ograniczenie `push` do `main` pozwala uniknąć dwóch skanów tej samej
zmiany: jednego z pushu gałęzi i drugiego z PR-a.

Krok **Run Semgrep**:

```yaml
      - name: Run Semgrep
        run: semgrep scan --error --config rules/java-sqli-demo.yml app/
```

Lokalna reguła daje kontrolowany przykład bez pobierania reguł `auto`.
Flaga `--error` powoduje nieudany krok po wykryciu problemu.

Krok **Run policy checks**:

```yaml
      - name: Run policy checks
        run: conftest test --rego-version v1 infra/deployment.yaml --policy policies/
```

Pozostaw pozostałe kroki instalacji i wykonaj próbę całego workflow.
Przed wystąpieniem warto przypiąć sprawdzone wersje narzędzi zamiast
polegać na najnowszej wersji pobieranej w dniu prezentacji.

Jeśli chcesz pokazać faktyczną blokadę przycisku scalania, ustaw
`security-pipeline` jako wymaganą kontrolę w regułach ochrony `main`
lub rulesecie, o ile plan i ustawienia repozytorium to umożliwiają.
Zrób to po pierwszym uruchomieniu, aby znać nazwę kontroli.
Nie ustawiaj `AI PR review` jako wymaganej bramki bezpieczeństwa.
Czerwony job i wymagana kontrola blokująca merge to dwie różne rzeczy.

### 3.4. Próba techniczna

- Potwierdź zielony pipeline na bezpiecznym `app/` na `main`.
- Wykonaj próbny PR; sprawdź komentarz AI i jego SHA.
- Sprawdź dostępność modelu, środki i limity konta API.
- Sprawdź instalację Conftest. Jeśli krok pobierania wydania nie działa,
  popraw go i przetestuj przed prezentacją.
- Otwórz w przeglądarce karty: kod repozytorium, **Pull requests**, **Actions**.
- Zachowaj zrzut lub gotowy próbny PR z wynikiem na wypadek niedostępności usług.
- Zamknij próbny PR i użyj innej nazwy gałęzi dla właściwego pokazu.

## 4. Scenariusz na żywo

### Etap A — wyjaśnij mechanizm, 2–3 minuty

Pokaż `.github/workflows/ai-review.yml` i wskaż:

- `on: pull_request` — zdarzenie uruchamiające automat;
- `runs-on: ubuntu-latest` — tymczasowa maszyna GitHuba;
- `ref: ...base.sha` — skrypt review pochodzi z zaufanej bazy;
- `run: python3 ai_review.py` — zwykłe polecenie wykonywane na maszynie;
- `secrets.OPENAI_API_KEY` — klucz dostarczany przez GitHub Secrets;
- `continue-on-error: true` — awaria review AI nie blokuje joba.

Komentarz do powiedzenia:

> „Nie stawiamy własnego serwera. GitHub wykonuje skrypt, a skrypt
> komunikuje się z API. Klucz jest w środowisku procesu, a model
> dostaje diff, nie token GitHuba ani klucz API.”

### Etap B — wprowadź podatność, 3 minuty

W terminalu:

```bash
git switch main
git pull --ff-only origin main
git switch -c demo/sql-injection-review
cp app_vuln/UserController.java app/UserController.java
git diff -- app/UserController.java
git add app/UserController.java
git commit -m "demo: introduce SQL injection for security review"
git push -u origin demo/sql-injection-review
```

Pokaż konkatenację `userId` do zapytania SQL i użycie `Statement`.
Wyjaśnij, że wejście użytkownika zaczyna wpływać na składnię zapytania.

Na GitHubie otwórz **Pull requests → New pull request**:

- base: `main`;
- compare: `demo/sql-injection-review`;
- tytuł: `Demo: SQL injection wykryte przez Semgrep i AI`;
- zwykły PR, nie draft.

Celowo podatnego PR-a nie scalaj.

### Etap C — pokaż wyniki, 4–5 minut

1. Otwórz **Actions → demo-pipeline**, wybierz uruchomienie dla PR-a
   i otwórz krok **Run Semgrep**.
2. Pokaż nazwę reguły, wskazany plik i wykryty wzorzec.
3. Przy konfiguracji z punktu 3.3 krok i job powinny być czerwone.
   Conftest będzie wtedy pominięty, ponieważ wcześniejszy krok zakończył się błędem.
4. Otwórz **Actions → AI PR review → review** i pokaż wykonanie skryptu.
5. Wróć do **Conversation** PR-a. Pokaż jeden komentarz `AI review`,
   analizowany commit i sugestię użycia `PreparedStatement`, jeśli model ją podał.

Wynik AI jest niedeterministyczny. Nie obiecuj identycznej treści ani
wykrycia problemu za każdym razem. Review pojawia się jako komentarz
w rozmowie, nie jako formalne „Approve” lub komentarze przypięte do linii.
Semgrep wypisuje wynik w logu kroku; nie publikujemy tu automatycznie SARIF
ani osobnego komentarza Semgrep.

Komentarz do powiedzenia:

> „Semgrep wykrywa wzorzec opisany regułą. AI próbuje wyjaśnić problem
> i zaproponować poprawkę. Oba wyniki trzeba interpretować; przejście
> skanu nie dowodzi, że cały system jest bezpieczny.”

### Etap D — popraw kod, 3–4 minuty

Na tej samej gałęzi:

```bash
cp app_fixed/UserController.java app/UserController.java
git diff -- app/UserController.java
git add app/UserController.java
git commit -m "demo: fix SQL injection with PreparedStatement"
git push
```

Pokaż placeholder `?`, `prepareStatement` i `setString`.
Wyjaśnij, że wartość parametru jest przekazywana oddzielnie od składni SQL.

Sprawdź nowe uruchomienia **Actions**:

- Semgrep powinien przejść dla tego przykładu.
- Conftest powinien przejść, jeśli manifest nadal ma limity CPU i pamięci,
  a instalacja narzędzia działa.
- Komentarz AI powinien zostać zaktualizowany i wskazywać nowy SHA.

**Pułapka pustego diffu:** jeśli plik po poprawce jest identyczny z plikiem
na `main` i w PR-ze nie ma innych zmian, diff PR-a będzie pusty.
Skrypt zaktualizuje komentarz informacją, że analiza AI nie została wykonana.
To prawidłowy wynik, nie potwierdzenie wykonania drugiego review przez model.
Jeżeli chcesz pokazać drugie wywołanie AI, przed commitem dodaj do poprawionej
metody krótki, sensowny komentarz, np. `// Bind user input as a SQL parameter.`
Wtedy PR zachowa niepusty diff względem bazy. Model ocenia bieżący diff PR-a,
a nie wyłącznie ostatni commit i nie historię kolejnych poprawek.

Nie mów, że AI naprawiło plik: w tym scenariuszu poprawkę wprowadziłeś ręcznie.

### Etap E — zakończenie, 1 minuta

Pokaż zieloną kontrolę bezpieczeństwa i komentarz z aktualnym SHA.
Zamknij demonstracyjny PR bez scalania i wróć lokalnie na `main`:

```bash
git switch main
```

Zdanie na koniec:

> „Workflow automatyzuje kontrolę każdej zmiany. Reguły dają powtarzalną
> kontrolę konkretnych wzorców, AI dostarcza dodatkowych wskazówek,
> a człowiek sprawdza wynik i decyduje o scaleniu.”

## 5. Wariant dodatkowy: polityka infrastruktury, 2–3 minuty

Na osobnej gałęzi utworzonej z bezpiecznego `main` usuń tylko
`resources.limits.memory` z `infra/deployment.yaml`, wyślij zmianę i otwórz PR.
Nie dodawaj jednocześnie SQL injection, aby Semgrep nie zatrzymał joba wcześniej.

Oczekiwany wynik: Semgrep przechodzi, a Conftest zgłasza
`Container must define memory limit`. Przywróć `memory: "256Mi"` pod
`resources.limits`, zacommituj i wyślij. Kontrola powinna wrócić do zielonego
wyniku. Zamknij PR po pokazie.

To osobna kontrola polityki zasobów — manifest jest materiałem do testu
Conftest, a workflow nie wdraża go do klastra Kubernetes.

## 6. Rozwiązywanie problemów podczas próby

| Objaw | Co sprawdzić |
| --- | --- |
| Brak workflow w Actions | Czy `.github/workflows/` jest w katalogu głównym i pliki są wypchnięte? |
| Job AI ma status skipped | Czy PR jest draftem, pochodzi z forka lub uruchomił go Dependabot? |
| Zielony job AI, ale brak nowego komentarza | Otwórz log kroku. Brak sekretu pomija analizę; `continue-on-error` może ukryć błąd API w ogólnym wyniku joba. |
| `AI review skipped: configure...` | Dodaj sekret o dokładnej nazwie `OPENAI_API_KEY`. |
| HTTP 401 | Sprawdź klucz i jego ważność; nie wypisuj go do logów. |
| HTTP 403 | Sprawdź, które API zgłosiło błąd: uprawnienia tokena GitHuba, politykę organizacji lub dostęp do usługi. |
| HTTP 429 | Sprawdź limity i dostępne środki konta API; nie ponawiaj bez końca. |
| Błąd modelu / HTTP 404 | Sprawdź dostęp konta do modelu oraz `OPENAI_REVIEW_MODEL`. |
| `ai_review.py` nie istnieje | Skrypt musi być obecny w bazie PR-a, nie tylko na jego gałęzi. |
| Review odrzucone jako nieaktualne | Wysłano nowszy commit lub zamknięto PR; sprawdź najnowsze uruchomienie. |
| SQL injection, ale Semgrep zielony | Sprawdź `--error`, lokalną regułę, skanowanie `app/` oraz SHA uruchomienia. |
| Błąd pobierania Conftest | Sprawdź log instalacji i adres wydania; to nie wynik polityki. |
| Brak ponownej analizy AI po poprawce | Sprawdź, czy PR ma jeszcze niepusty diff względem bazy. |

Przy awarii usługi pokaż wynik wcześniej przygotowanej próby,
wyraźnie zaznaczając, że pochodzi z poprzedniego uruchomienia.
Workflow AI nie ma deterministycznego fallbacku; taki fallback występuje
w osobnym `ai_fix.py`, a nie w `ai_review.py`.

## 7. Limity skonfigurowane w tym demo

- Maksymalny czas joba review: 5 minut.
- Najwyżej jedno wywołanie modelu na uruchomienie skryptu.
- Budżet wybranych patchy: 40 000 znaków; duże pliki i pliki bez patcha są pomijane.
- Maksymalna odpowiedź: 2500 tokenów; model proszony jest o najwyżej pięć uwag.
- Nowe uruchomienie review tego samego PR-a anuluje poprzednie.
- API OpenAI jest rozliczane osobno od GitHub Actions.
- To nie jest miesięczny limit wydatków; każdy nowy commit może uruchomić review.

## 8. Ściąga dla prowadzącego

1. Przed pokazem: workflow i reviewer na `main`, sekret dodany, próba udana.
2. Pokaż YAML i polecenie `python3 ai_review.py`.
3. Nowa gałąź → skopiuj `app_vuln` do `app` → commit → push → PR.
4. Pokaż log Semgrep i komentarz AI.
5. Skopiuj `app_fixed` do `app` → commit → push.
6. Pokaż nowe wyniki, aktualny SHA i ewentualny pusty diff.
7. Zamknij PR bez scalania.

Materiały:

- [GitHub: zdarzenia uruchamiające workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)
- [GitHub: konfiguracja sekretów](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Opis projektu](README.md)
