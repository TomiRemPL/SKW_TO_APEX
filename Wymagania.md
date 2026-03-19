# Założenia wstępne - rozszerzenie funkcjonalności SkwToAPEX

- Plik **`SKW_TO_APEX_DDL.sql`** zawiera kod DDL tworzący obiekty obecnego projektu.
- Katalog **`program`** to kod obecnej wersji aplikacji w APEX - przy eksporcie użyto opcji 'readable' - czytelna struktura projektu w poszczególnych podkatalogach i odpowiednich plikach.

Cześć z wymagań została już zrealizowana.


## Wymagania odnośnie rozwoju aplikacji

### Wczytanie danych do tabeli `B_KONTROLA`

1. **Cykliczne odświeżanie**
   - Dane w tabeli `B_KONTROLA` będą odświeżane 1‑raz w miesiącu (lub rzadziej).
   - Wczytywany zestaw zawsze zawiera komplet rekordów – nowe kontrole oraz modyfikacje istniejących.
   - Kluczem w zewnętrznej aplikacji jest pole `REFERENCE_ID`. W tabeli źródłowej i wczytywanej jest ono unikalne.

2. **Mechanizm wczytu**
   - Operacja będzie wywoływana poprzez nową stronę w APEX (dodam ją ręcznie).
   - Podczas wczytu naleŝy:
     - Sprawdzić, czy rekord o danym `REFERENCE_ID` już istnieje w `B_KONTROLA`.
     - Jeżeli istnieje – porównać wartości następujących pól:

       ```
       STATUS, CONTROL_LEVEL,
       DESCRIPTION_FR_, DESCRIPTION_EN_,
       SHORT_DESCRIPTION_FR_, SHORT_DESCRIPTION_EN_,
       DEFINITION_FR_, DEFINITION_EN_,
       OBJECTIVE_FR_, OBJECTIVE_EN_,
       DOMAIN_PROCESS, RISKS, CONTROL_GROUP
       ```

     - Jeśli wykryto **zmiany** → zapisać obecną wersję w tabeli historycznej (z informacjami kto i kiedy), a w tabeli głównej zaktualizować pola.
       — **ID_PK_B_KONTROLA** nie zmienia się przy aktualizacji.
     - Jeśli w wczytanym zbiorze brak `REFERENCE_ID` istniejącego rekordu → ustawić w bazie `STATUS = 'Deactive'` oraz zapisać datę od kiedy jest nieaktywny.
       Rekord pozostaje nieaktywny do momentu, gdy pojawi się ponownie w kolejnym imporcie.
     - Jeśli pojawi się rekord z **nieistniejącym** `REFERENCE_ID` → utworzyć nowy wpis.

### Warstwa raportowa i logi

- Udostępnić statystyki dla każdego wczytu:
  - liczba rekordów wczytanych,
  - liczba dodanych,
  - liczba zmodyfikowanych.

### Dodawanie kolejnego audytu

 - Po wprowadzeniu danych koejnego audytu, użytkownik powinien mieć możliwość wyszukiwania konkretnych kontroli według różnych kryteriów, oraz oznaczać kontrole, które finalnie zostaną dodane do listy kontroli sprawdzanych w ramach danego audytu.
 - Użytkonik powinien móc w dowolnym czasie dodać lub usunąć kontrole objęte badaniem.
 - Na ekranie odnośnie przeprowadzonych audytów (brakuje tego ekranu w obecnym rozwiązaniu) powinien być przycisk, po naciśnięciu którego następuje "zamrożenie" zamina w kontekście dodawanych i usuwanych kontroli.
 - powiniem również być inny przycisk, który widzi tylko szef misji (jego login powinien być zapisywany w momencie tworzenia rekordu audytu).
 - dodatkowo dane w konkretnym audycie mogą edytować tylko szef misji oraz audytorzy, których loginy zostaną dodane do nowego pola w tabeli z audytami.
 - Inne osoby z dostępem do aplikacji powinny mieć tylko możliwość przeglądania danych.

## Uwagi ogólne

- Przemyśl zaproponowane rozwiązania i daj znać, jeśli chcesz coś zmienić lub rozszerzyć.
- Wynikiem ma być plik **SQL** zawierający:
  - wszystkie zmiany w strukturze danych,
  - nową tabelę np. przejściową do importu,
  - pakiet z funkcjami obsługującymi cały proces.
- Dołącz również **instrukcję wdrażania zmian** i dalszych kroków, w tym dodawania/konfiguracji ekranów w APEX (ekrany dodam ja, według Twoich wytycznych).
- Zweryfikuj proponowane modyfikacje, aby mieć pewność, że wszystko zadziała.

