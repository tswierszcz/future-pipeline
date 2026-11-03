# Demo: Security is Architecture + AI Fix

To repo zawiera 2 tryby:

1. `pipeline_fail.sh`  
   Pokazuje klasyczny fail pipeline po wykryciu podatności przez Semgrep.

2. `pipeline_ai_fix.sh`  
   Pokazuje flow:
   - Semgrep wykrywa problem
   - AI próbuje naprawić kod
   - Semgrep uruchamia się ponownie
   - pipeline przechodzi dalej

## Wymagania

- semgrep
- conftest
- bash
- python 3.10+

Opcjonalnie:
- `OPENAI_API_KEY` jeśli chcesz użyć prawdziwego modelu OpenAI
- pakiet Python `openai`:
```bash
python3 -m pip install openai
```

Bez `OPENAI_API_KEY` skrypt przejdzie na przewidywalny fallback demo.
Jeśli `OPENAI_API_KEY` jest ustawiony, ale pakiet `openai` nie jest zainstalowany, skrypt też przejdzie na fallback demo.

## Uruchomienie
Idz do katalgou src
```bash
source venv/bin/activate
```

Nadaj prawa:
```bash
chmod +x pipeline_fail.sh pipeline_ai_fix.sh
```

### 1. Wersja fail
```bash
./pipeline_fail.sh
```

### 2. Wersja AI fix
```bash
./pipeline_ai_fix.sh
```

Z prawdziwym wywołaniem OpenAI:
```bash
export OPENAI_API_KEY=...
python3 -m pip install openai
./pipeline_ai_fix.sh
```

### 3. Wersja PASS na poprawionym kodzie
```bash
./pipeline_fail.sh app_fixed
```

## Ważne

`app/` jest katalogiem roboczym.  
Skrypt `pipeline_ai_fix.sh` nadpisuje `app/UserController.java`.

Jeśli chcesz wrócić do wersji podatnej:
```bash
cp app_vuln/UserController.java app/UserController.java
```

## AI review pull requestów w GitHub Actions

Workflow `.github/workflows/ai-review.yml` analizuje diff PR-a przez OpenAI
i publikuje jeden komentarz po polsku. Kolejne commity aktualizują ten sam
komentarz. Review jest doradcze: nie zatwierdza PR-a, nie zmienia kodu i nie
blokuje scalenia z powodu uwag modelu. Błąd API jest widoczny w logu kroku,
ale dzięki `continue-on-error` nie blokuje joba. Nie ustawiaj tego workflow
jako wymaganej kontroli bezpieczeństwa.

### Konfiguracja

1. Umieść zawartość tego katalogu w głównym katalogu repozytorium GitHub
   (tak, aby `.github/workflows/` było bezpośrednio w jego katalogu głównym).
2. Dodaj i scal te pliki do gałęzi docelowej, zanim otworzysz demonstracyjny PR.
   Workflow uruchamia `ai_review.py` z commita bazowego PR-a, a nie z jego kodu.
3. W **Settings → Secrets and variables → Actions → Secrets** dodaj sekret
   `OPENAI_API_KEY` z kluczem konta API posiadającego dostęp do modelu i środki.
4. Opcjonalnie w zakładce **Variables** ustaw `OPENAI_REVIEW_MODEL`.
   Domyślnie używany jest `gpt-4.1-mini`.
5. Otwórz PR z gałęzi w tym samym repozytorium. Workflow uruchomi się przy
   otwarciu, ponownym otwarciu, nowych commitach oraz oznaczeniu jako gotowy.

Token `GITHUB_TOKEN` jest dostarczany automatycznie przez Actions. Workflow
deklaruje `contents: read` oraz `pull-requests: write`, potrzebne do pobierania
zmian i komentowania. Polityka organizacji musi pozwalać na te uprawnienia.
Brak sekretu powoduje pominięcie analizy z komunikatem w logu. PR-y robocze,
PR-y z forków i uruchomienia przez Dependabot są pomijane. Nie używamy
`pull_request_target` ani nie wykonujemy kodu z PR-a.

### Scenariusz prezentacji

1. Zacznij od poprawionego `app/UserController.java` na gałęzi docelowej.
2. Na nowej gałęzi wprowadź SQL injection:
   `cp app_vuln/UserController.java app/UserController.java`.
3. Zacommituj zmianę, wypchnij gałąź i otwórz PR. Sprawdź **Actions → AI PR review**
   oraz komentarz z analizą i propozycją użycia `PreparedStatement`.
4. Przywróć poprawkę przez `cp app_fixed/UserController.java app/UserController.java`,
   zacommituj i wypchnij. Komentarz zostanie zaktualizowany dla nowego commita.

Model może przeoczyć błąd albo zgłosić nietrafioną uwagę. Wynik prezentacji
nie jest deterministyczny. Semgrep i Conftest działają niezależnie;
`demo.yml` uruchamia Semgrep z lokalną regułą i `--error` przy PR-ach oraz pushach do `main`.

### Zakres i ograniczenia

- Do API OpenAI trafiają nazwy plików i patche wraz z kontekstem dostarczonym
  przez GitHub. Analiza nie pobiera całych plików ani całego repozytorium.
  Wysyłaj wyłącznie kod, który możesz przekazać do tego API; sekretów nie
  umieszczaj w commitach. `store: false` wyłącza przechowywanie odpowiedzi
  jako zasobu Responses; nie jest deklaracją zerowej retencji wszystkich danych API.
- Jedno uruchomienie wykonuje najwyżej jedno wywołanie modelu, z limitem
  40 000 znaków wybranych patchy i 2500 tokenów odpowiedzi. To ograniczenie
  rozmiaru, nie sztywny limit kosztu w walucie. Zbyt duże patche i pliki bez
  patcha są pomijane i ujawniane w komentarzu. Przekroczenie limitu 3000 plików
  GitHub kończy analizę błędem bez publikacji.
- Kod i nazwy plików są niezaufanymi danymi. Prompt zabrania wykonywania
  instrukcji zawartych w diffie, a model nie otrzymuje narzędzi ani tokenów.
  To ogranicza skutki prompt injection, ale nie gwarantuje poprawności review.
- Komentarz zawiera SHA analizowanego commita. Skrypt sprawdza aktualność PR-a
  przed analizą i publikacją; kolejne uruchomienia dla tego PR-a anulują poprzednie.
- Celowo podatne przykłady w `app_vuln/` i `vuln/` są oznaczone w instrukcji
  modelu jako materiał demonstracyjny.
- Skrypt używa standardowej biblioteki Pythona 3.10+, bez dodatkowych pakietów.

Nie zapisuj klucza w `pipeline_ai_fix.sh`; skrypt pobiera go teraz ze środowiska.
Jeśli poprzednio zapisany klucz był prawdziwy, unieważnij go i utwórz nowy.
Usunięcie go z pliku nie usuwa kopii z wcześniejszych commitów.

Testy bez sieci i bez kluczy:

```bash
python3 -m unittest discover -s tests -v
```

Dokumentacja API: [OpenAI — generowanie tekstu](https://developers.openai.com/api/docs/guides/text).
Zdarzenia workflow: [GitHub — pull_request](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#pull_request).
# future-pipeline
