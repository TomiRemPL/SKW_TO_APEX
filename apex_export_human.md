# Aplikacja SKW_2_APEX (Working Copy: tr_20260318) (ID: 338, alias: START338141)

## Strony użytkownika

### Strona 1: Home
- **Tytuł:** SKW_2_APEX
- **Tryb:** Normal
- **Uwierzytelnianie:** Page Requires Authentication

#### Region: My Info
- **Typ:** Static Content

#### Region: Copyright
- **Typ:** Static Content

#### Region: Tytuł — "SKW_2_APEX by DAW"
- **Typ:** Static Content

---

### Strona 2: DAW_ANKIETA
- **Tryb:** Normal
- **Uwierzytelnianie:** Page Requires Authentication

#### Region: Przerywnik
- **Typ:** Static Content

#### Region: P2_SKUTECZNOSC_OCENA
- **Typ:** Interactive Grid (edytowalny: Update Row)
- **Źródło SQL:**
```sql
SELECT * FROM B_OCENA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = 2 /*skuteczność*/

```

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| B_OCENA_PRZELAMANA_UZASADNIENIE | Textarea | Przełamanie - komentarz | B_OCENA_PRZELAMANA_UZASADNIENIE | — | — |
| B_OCENA_CZY_NADPISANA | Switch | Czy przełamanie? | B_OCENA_CZY_NADPISANA | — | — |
| B_OCENA_NADPISANA | Number Field | Ocena nadpisana: | B_OCENA_NADPISANA | — | — |
| B_OCENA_LICZONA | Number Field | Ocena wyliczona: | B_OCENA_LICZONA | — | — |
| ID_PK_B_OCENA | Hidden | — | ID_PK_B_OCENA | tak | — |
| B_SL_C_PYTANIE_DZIEDZINA_ID | Hidden | — | B_SL_C_PYTANIE_DZIEDZINA_ID | — | — |
| ID_FK_B_KONTROLA | Hidden | — | ID_FK_B_KONTROLA | — | — |
| ID_FK_B_AUDYT | Hidden | — | ID_FK_B_AUDYT | — | — |
| APEX$ROW_ACTION | Actions Menu | — | — | — | — |
| APEX$ROW_SELECTOR | Row Selector | — | — | — | — |

#### Region: Przerywnik
- **Typ:** Static Content

#### Region: P2_SKUTECZNOSC — "Adekwatność"
- **Typ:** Interactive Grid (edytowalny: Update Row, Delete Row)
- **Źródło SQL:**
```sql
SELECT * FROM B_ANKIETA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = 2 /*Skuteczność*/

```

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| ID_PK_B_ANKIETA | Hidden | — | ID_PK_B_ANKIETA | tak | — |
| ID_FK_B_AUDYT | Hidden | — | ID_FK_B_AUDYT | — | — |
| ID_FK_B_KONTROLA | Hidden | — | ID_FK_B_KONTROLA | — | — |
| ID_FK_B_SL_C_PYTANIE | Hidden | — | ID_FK_B_SL_C_PYTANIE | — | — |
| B_SL_C_PYTANIE_WAGA | Hidden | — | B_SL_C_PYTANIE_WAGA | — | — |
| ID_FK_B_SL_C_PYTANIE_DZIEDZINA | Hidden | — | ID_FK_B_SL_C_PYTANIE_DZIEDZINA | — | — |
| SHORT_DESCRIPTION_FR_ | Hidden | — | SHORT_DESCRIPTION_FR_ | — | — |
| REFERENCE_ID | Hidden | — | REFERENCE_ID | — | — |
| B_ANKIETA_ODPOWIEDZ | Select List | Odpowiedź | B_ANKIETA_ODPOWIEDZ | — | — |
| B_ANKIETA_OCENA_WAZONA_LICZ | Number Field | Ocena ważona | B_ANKIETA_OCENA_WAZONA_LICZ | — | — |
| B_ANKIETA_KOMENTARZ | Textarea | Komentarz | B_ANKIETA_KOMENTARZ | — | — |
| B_ANKIETA_LINK_DOKUMENTACJA | Textarea | Link do dokumentacji | B_ANKIETA_LINK_DOKUMENTACJA | — | — |
| APEX$ROW_ACTION | Actions Menu | — | — | — | — |
| APEX$ROW_SELECTOR | Row Selector | — | — | — | — |
| DATA_OSTATNIEJ_KONTROLI_NA_MOMENT_AUDYTU | Date Picker | Data Ostatniej Kontroli Na Moment Audytu | DATA_OSTATNIEJ_KONTROLI_NA_MOMENT_AUDYTU | — | — |
| PYTANIE_TEKST | Display Only | Pytanie | — | — | — |
| PYTANIE_KOLEJNOSC | Display Only | — | — | — | — |

#### Region: P2_ADEKWATNOSC_OCENA
- **Typ:** Interactive Grid (edytowalny: Update Row)
- **Źródło SQL:**
```sql
SELECT * FROM B_OCENA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = 1 /*ADEKWATNOŚĆ*/

```

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| ID_FK_B_AUDYT | Hidden | — | ID_FK_B_AUDYT | — | — |
| ID_FK_B_KONTROLA | Hidden | — | ID_FK_B_KONTROLA | — | — |
| B_SL_C_PYTANIE_DZIEDZINA_ID | Hidden | — | B_SL_C_PYTANIE_DZIEDZINA_ID | — | — |
| ID_PK_B_OCENA | Hidden | — | ID_PK_B_OCENA | tak | — |
| B_OCENA_LICZONA | Number Field | Ocena wyliczona: | B_OCENA_LICZONA | — | — |
| B_OCENA_NADPISANA | Number Field | Ocena nadpisana: | B_OCENA_NADPISANA | — | — |
| APEX$ROW_ACTION | Actions Menu | — | — | — | — |
| APEX$ROW_SELECTOR | Row Selector | — | — | — | — |
| B_OCENA_CZY_NADPISANA | Switch | Czy przełamanie? | B_OCENA_CZY_NADPISANA | — | — |
| B_OCENA_PRZELAMANA_UZASADNIENIE | Textarea | Przełamanie - komentarz | B_OCENA_PRZELAMANA_UZASADNIENIE | — | — |

#### Region: P2_ADEKWATNOSC — "Adekwatność"
- **Typ:** Interactive Grid (edytowalny: Update Row, Delete Row)
- **Źródło SQL:**
```sql
SELECT * FROM B_ANKIETA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = 1 /*ADEKWATNOŚĆ*/

```

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| APEX$ROW_SELECTOR | Row Selector | — | — | — | — |
| APEX$ROW_ACTION | Actions Menu | — | — | — | — |
| PYTANIE_TEKST | Display Only | Pytanie | — | — | — |
| ID_PK_B_ANKIETA | Hidden | — | ID_PK_B_ANKIETA | tak | — |
| ID_FK_B_AUDYT | Hidden | — | ID_FK_B_AUDYT | — | — |
| ID_FK_B_KONTROLA | Hidden | — | ID_FK_B_KONTROLA | — | — |
| ID_FK_B_SL_C_PYTANIE | Hidden | — | ID_FK_B_SL_C_PYTANIE | — | — |
| B_SL_C_PYTANIE_WAGA | Hidden | — | B_SL_C_PYTANIE_WAGA | — | — |
| ID_FK_B_SL_C_PYTANIE_DZIEDZINA | Hidden | — | ID_FK_B_SL_C_PYTANIE_DZIEDZINA | — | — |
| SHORT_DESCRIPTION_FR_ | Hidden | — | SHORT_DESCRIPTION_FR_ | — | — |
| REFERENCE_ID | Hidden | — | REFERENCE_ID | — | — |
| B_ANKIETA_ODPOWIEDZ | Select List | Odpowiedź | B_ANKIETA_ODPOWIEDZ | — | — |
| B_ANKIETA_OCENA_WAZONA_LICZ | Number Field | Ocena ważona | B_ANKIETA_OCENA_WAZONA_LICZ | — | — |
| B_ANKIETA_KOMENTARZ | Textarea | Komentarz | B_ANKIETA_KOMENTARZ | — | — |
| B_ANKIETA_LINK_DOKUMENTACJA | Textarea | Link do dokumentacji | B_ANKIETA_LINK_DOKUMENTACJA | — | — |
| DATA_OSTATNIEJ_KONTROLI_NA_MOMENT_AUDYTU | Date Picker | Data Ostatniej Kontroli Na Moment Audytu | DATA_OSTATNIEJ_KONTROLI_NA_MOMENT_AUDYTU | — | — |
| PYTANIE_KOLEJNOSC | Display Only | — | — | — | — |

#### Elementy formularza

| Nazwa | Typ | Etykieta | Kolumna | LOV |
|-------|-----|----------|---------|-----|
| P2_AUDYT_ID | Select List | Numer Audytu | — | B_AUDYT.B_AUDYT_NUMER_AUDYTU |
| P2_KONTROLA_ID | Select List | Numer Kontroli | — | B_LISTA_KONTROLI_DO_AUDYTU |

#### Przyciski

- **WyliczOcenę** — ? [Submit Page] **(primary)**

#### Procesy

**P2_ADEKWATNOSC - DMI** (Processing)

**WyliczenieOceny - SKUTECZNOSC** (Processing, język: PL/SQL)

```plsql
DECLARE
    v_dziedzina NUMBER := 2; /*SKUTECZNOSC*/
	v_liczba_null 	NUMBER;
	v_liczba_na 	NUMBER;
    v_suma      	NUMBER;
    v_id_audytu 	NUMBER := :B_APP_ID_AUDYT; 
    v_wynik         NUMBER := -1;
BEGIN
    --0. sprawdzenie, czy wszystkie pola mają ustawioną jakąś wartość
	SELECT count(1) 
	INTO v_liczba_null
	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ IS NULL;
	-- IF v_liczba_null>0 THEN 
	--   v_wynik := NULL;
	-- END IF;
	-- 1. CZEŚĆ: Sprawdzenie, czy wszystkie 6 rekordów ma status 'N/A'
    SELECT COUNT(1)
    INTO v_liczba_na
 	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ='N/A';
    -- Jeśli licznik zwróci 6 (lub więcej), zwracamy 'N/A'
    -- IF v_liczba_na >= 6 THEN
    --     v_wynik := -1;
    -- END IF;
    -- -- 3. CZEŚĆ: Sumowanie kolumny z bazy danych
    SELECT SUM(a.B_ANKIETA_OCENA_WAZONA_LICZ) -- Twoja kolumna F
    INTO v_suma
 	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ IS NOT NULL;
    -- Zabezpieczenie: Jeśli suma jest NULL (brak rekordów), traktuj jak 0
    v_suma := NVL(v_suma, 0);
    -- 4. CZEŚĆ: Ocena końcowa na podstawie sumy
    if v_liczba_null > 0 then v_wynik := null;
    ELSIF v_liczba_na = 6 then v_wynik := -1;
    ELSIF v_suma < 0.25 THEN   v_wynik := 4;
    ELSIF v_suma < 0.5 THEN    v_wynik := 3;
    ELSIF v_suma <= 0.75 THEN  v_wynik := 2;
    ELSE  v_wynik := 1;
    END IF;
    
    /*Zapisanie wyliczonej oceny do bazy danych*/
    UPDATE B_OCENA a   
     SET a.B_OCENA_LICZONA = v_wynik     
    WHERE 1=1
    AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
    AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
    AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = v_dziedzina; /*ADEKWATNOŚĆ*/ 

    /*Jeśli pole B_OCENA_CZY_NADPISANA ma wartość 1 - TAK, to nie przepisujemy wyniku, w
     w przeciwnym przypadku przepisujemy*/
    --if :B_OCENA_CZY_NADPISANA = 'NIE' then
        UPDATE B_OCENA a   
         SET a.B_OCENA_NADPISANA = v_wynik     
        WHERE 1=1
        AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
        AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
        AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = v_dziedzina /*ADEKWATNOŚĆ*/ 
        AND nvl(A.B_OCENA_CZY_NADPISANA,-1) = 0;
    --END IF;
END;	

```

**P2_SKUTECZNOSC - DMI** (Processing)

**P2_SKUTECZNOSC - Save Interactive Grid Data** (Processing)

**P2_ADEKWATNOSC_OCENA - Save Interactive Grid Data** (Processing)

**WyliczenieOceny - ADEKWATNOSC** (Processing, język: PL/SQL)

```plsql
DECLARE
    v_dziedzina NUMBER := 1; /*adekwatność*/
	v_liczba_null 	NUMBER;
	v_liczba_na 	NUMBER;
    v_suma      	NUMBER;
    v_id_audytu 	NUMBER := :B_APP_ID_AUDYT; 
    v_wynik         NUMBER := -1;
BEGIN
    --0. sprawdzenie, czy wszystkie pola mają ustawioną jakąś wartość
	SELECT count(1) 
	INTO v_liczba_null
	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ IS NULL;
	-- IF v_liczba_null>0 THEN 
	--   v_wynik := NULL;
	-- END IF;
	-- 1. CZEŚĆ: Sprawdzenie, czy wszystkie 6 rekordów ma status 'N/A'
    SELECT COUNT(1)
    INTO v_liczba_na
 	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ='N/A';
    -- Jeśli licznik zwróci 6 (lub więcej), zwracamy 'N/A'
    -- IF v_liczba_na >= 6 THEN
    --     v_wynik := -1;
    -- END IF;
    -- -- 3. CZEŚĆ: Sumowanie kolumny z bazy danych
    SELECT SUM(a.B_ANKIETA_OCENA_WAZONA_LICZ) -- Twoja kolumna F
    INTO v_suma
 	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ IS NOT NULL;
    -- Zabezpieczenie: Jeśli suma jest NULL (brak rekordów), traktuj jak 0
    v_suma := NVL(v_suma, 0);
    -- 4. CZEŚĆ: Ocena końcowa na podstawie sumy
    if v_liczba_null > 0 then v_wynik := null;
    ELSIF v_liczba_na = 6 then v_wynik := -1;
    ELSIF v_suma < 0.25 THEN   v_wynik := 4;
    ELSIF v_suma < 0.5 THEN    v_wynik := 3;
    ELSIF v_suma <= 0.75 THEN  v_wynik := 2;
    ELSE  v_wynik := 1;
    END IF;
    
    /*Zapisanie wyliczonej oceny do bazy danych*/
    UPDATE B_OCENA a   
     SET a.B_OCENA_LICZONA = v_wynik     
    WHERE 1=1
    AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
    AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
    AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = v_dziedzina; /*ADEKWATNOŚĆ*/ 

    /*Jeśli pole B_OCENA_CZY_NADPISANA ma wartość 1 - TAK, to nie przepisujemy wyniku, w
     w przeciwnym przypadku przepisujemy*/
    --if :B_OCENA_CZY_NADPISANA = 'NIE' then
        UPDATE B_OCENA a   
         SET a.B_OCENA_NADPISANA = v_wynik     
        WHERE 1=1
        AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
        AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
        AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = v_dziedzina /*ADEKWATNOŚĆ*/ 
        AND nvl(A.B_OCENA_CZY_NADPISANA,-1) = 0;
    --END IF;
END;	

```

#### Akcje dynamiczne

- **Oblicz ocenę ważoną AD** — zdarzenie: Change
  - Krok: Set Value
- **Ustawienie B_APP_ID_AUDYT** — zdarzenie: Change
  - Krok: Execute Server-side Code
    ```
    begin
  :B_APP_ID_AUDYT := :P2_AUDYT_ID;
end;

    ```
  - Krok: Refresh
    - Wpływa na: jQuery Selector: .odswiez-mnie
- **Ustawienie B_APP_ID_KONTROLI** — zdarzenie: Change
  - Krok: Execute Server-side Code
    ```
    Begin
  :B_APP_ID_KONTROLI := :P2_KONTROLA_ID;
End;

    ```
  - Krok: Refresh
    - Wpływa na: jQuery Selector: .odswiez-mnie
- **Oblicz ocenę ważoną SK** — zdarzenie: Change
  - Krok: Set Value
  - Krok: Execute Server-side Code
    ```
    DECLARE
    v_dziedzina NUMBER := 1; /*adekwatność*/
	v_liczba_null 	NUMBER;
	v_liczba_na 	NUMBER;
    v_suma      	NUMBER;
    v_id_audytu 	NUMBER := :B_APP_ID_AUDYT; -- Zakładam, że ID audytu jest w tej zmiennej
    v_wynik         NUMBER := -1;
BEGIN
    --0. sprawdzenie, czy wszystkie pola mają ustawioną jakąś wartość
	SELECT count(1) 
	INTO v_liczba_null
	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ IS NULL;
	IF v_liczba_null>0 THEN 
	  v_wynik := NULL;
	END IF;
	-- 1. CZEŚĆ: Sprawdzenie, czy wszystkie 6 rekordów ma status 'N/A'
    SELECT COUNT(1)
    INTO v_liczba_na
 	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ='N/A';
    -- Jeśli licznik zwróci 6 (lub więcej), zwracamy 'N/A'
    IF v_liczba_na >= 6 THEN
        v_wynik := -1;
    END IF;
    -- 3. CZEŚĆ: Sumowanie kolumny z bazy danych
    SELECT SUM(a.B_ANKIETA_OCENA_WAZONA_LICZ) -- Twoja kolumna F
    INTO v_suma
 	FROM B_ANKIETA a
	WHERE 
	  A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = v_dziedzina
      AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
      AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
      AND a.B_ANKIETA_ODPOWIEDZ IS NOT NULL;
    -- Zabezpieczenie: Jeśli suma jest NULL (brak rekordów), traktuj jak 0
    v_suma := NVL(v_suma, 0);
    -- 4. CZEŚĆ: Ocena końcowa na podstawie sumy
    IF v_suma < 0.25 THEN
        v_wynik := 4;
    ELSIF v_suma < 0.5 THEN
        v_wynik := 3;
    ELSIF v_suma <= 0.75 THEN
        v_wynik := 2;
    ELSE
        v_wynik := 1;
    END IF;
    
    UPDATE B_OCENA a   -- <--- ZMIEŃ NA NAZWĘ TABELI GDZIE TRZYMASZ WYNIK CAŁEGO AUDYTU
    SET a.B_OCENA_LICZONA = v_wynik     -- <--- ZMIEŃ NA NAZWĘ KOLUMNY Z WYNIKIEM
    WHERE 1=1
    AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
    AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
    AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = v_dziedzina; /*ADEKWATNOŚĆ*/   
END;

    ```

#### CSS strony

```css
.tekst-zawijany {
    white-space: pre-wrap !important;
    min-width: 150px; /* Opcjonalnie: minimalna szerokość kolumny */
}

```

---

### Strona 3: DAW_WYSZUKIWANIE
- **Tryb:** Normal
- **Uwierzytelnianie:** Page Requires Authentication

#### Region: Search Results
- **Typ:** Classic Report
- **Źródło:** tabela `B_KONTROLA`

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| ID_PK_B_KONTROLA | Hidden | — | — | — | — |
| REFERENCE_ID | Plain Text | Reference ID | — | — | — |
| DATA_OSTATNIEJ_KONTROLI | Hidden | — | — | — | — |
| DATA_PIERWSZEJ_KONTROLI | Hidden | — | — | — | — |
| LICZBA_WYKONANYCH_KONTROLI | Hidden | — | — | — | — |
| STATUS | Plain Text | Status | — | — | — |
| CONTROL_LEVEL | Plain Text | Control Level | — | — | — |
| DESCRIPTION_FR_ | Plain Text | Description Fr | — | — | — |
| DESCRIPTION_EN_ | Plain Text | Description En | — | — | — |
| SHORT_DESCRIPTION_FR_ | Plain Text | Short Description Fr | — | — | — |
| SHORT_DESCRIPTION_EN_ | Plain Text | Short Description En | — | — | — |
| DEFINITION_FR_ | Hidden | — | — | — | — |
| DEFINITION_EN_ | Hidden | — | — | — | — |
| OBJECTIVE_FR_ | Hidden | — | — | — | — |
| OBJECTIVE_EN_ | Hidden | — | — | — | — |
| DOMAIN_PROCESS | Plain Text | Domain Process | — | — | — |
| RISKS | Plain Text | Risks | — | — | — |
| CONTROL_GROUP | Plain Text | Control Group | — | — | — |

#### Region: Search
- **Typ:** Smart Filters

---

### Strona 4: DAW_LISTA_AUDYTOW
- **Tryb:** Normal
- **Uwierzytelnianie:** Page Requires Authentication

#### Region: Breadcrumb
- **Typ:** Breadcrumb

#### Region: filtry-kontroli — "Filtry wyszukiwania"
- **Typ:** Static Content

#### Region: ListaAudytow
- **Typ:** Interactive Grid (edytowalny: Add Row, Update Row, Delete Row)
- **Źródło:** tabela `B_AUDYT`

| Kolumna | Typ | Nagłówek | Źródło | PK | Link |
|---------|-----|----------|--------|----|------|
| ID_PK_B_AUDYT | Hidden | — | ID_PK_B_AUDYT | tak | — |
| B_AUDYT_NUMER_AUDYTU | Link | B Audyt Numer Audytu | B_AUDYT_NUMER_AUDYTU | — | →strona 6 |
| STATUS_AUDYTU | Text Field | Status Audytu | STATUS_AUDYTU | — | — |
| SZEF_MISJI_LOGIN | Text Field | Szef Misji Login | SZEF_MISJI_LOGIN | — | — |
| AUDYTORZY_LOGINY | Textarea | Audytorzy Loginy | AUDYTORZY_LOGINY | — | — |
| DATA_UTWORZENIA | Date Picker | Data Utworzenia | DATA_UTWORZENIA | — | — |
| DATA_ZAMROZENIA | Date Picker | Data Zamrozenia | DATA_ZAMROZENIA | — | — |
| DATA_ZAKONCZENIA | Date Picker | Data Zakonczenia | DATA_ZAKONCZENIA | — | — |
| ZAMROZIL_LOGIN | Text Field | Zamrozil Login | ZAMROZIL_LOGIN | — | — |
| ZAKONCZYL_LOGIN | Text Field | Zakonczyl Login | ZAKONCZYL_LOGIN | — | — |
| LiczbSprawdzanychKontroli | Display Only | — | — | — | — |
| APEX$ROW_SELECTOR | Row Selector | — | — | — | — |
| APEX$ROW_ACTION | Actions Menu | — | — | — | — |

#### Elementy formularza

| Nazwa | Typ | Etykieta | Kolumna | LOV |
|-------|-----|----------|---------|-----|
| P4_FILTR_REFERENCE_ID | Text Field | Filtr Reference Id | — | — |

#### Procesy

**ListaAudytow - Save Interactive Grid Data** (Processing)

---

### Strona 5: DAW_IMPORT_KONTROLI
- **Tryb:** Normal
- **Uwierzytelnianie:** Page Requires Authentication

#### Elementy formularza

| Nazwa | Typ | Etykieta | Kolumna | LOV |
|-------|-----|----------|---------|-----|
| P_ID_LOG_WYNIKU | Hidden | — | — | — |
| P_PLIK | File Upload | Plik do wczytania - Excel | — | — |

#### Przyciski

- **WczytajPlik** — ? [Submit Page]

#### Procesy

**Wczyt** (Before Header, język: PL/SQL)

```plsql
DECLARE
    v_id_log    NUMBER;
    v_id_sesji  NUMBER;
BEGIN
    -- Wygeneruj unikalny ID sesji importu
    SELECT NVL(MAX(ID_SESJI_IMPORTU), 0) + 1
    INTO   v_id_sesji
    FROM   B_KONTROLA_IMPORT;

    -- Wczytaj dane z pliku Excel do tabeli stagingowej.
    -- APEX_DATA_PARSER.PARSE czyta plik bezposrednio z APEX_APPLICATION_TEMP_FILES
    -- (gdzie APEX odkłada plik po wgraniu przez FILE BROWSE).
    -- p_skip_rows => 1 pomija pierwszy wiersz z naglowkami kolumn.
    -- p_file_type => APEX_DATA_PARSER.C_FILE_TYPE_XLSX wymusza format Excel.
    INSERT INTO B_KONTROLA_IMPORT (
        ID_SESJI_IMPORTU,
        REFERENCE_ID,           STATUS,
        CONTROL_LEVEL,          DESCRIPTION_FR_,
        DESCRIPTION_EN_,        SHORT_DESCRIPTION_FR_,
        SHORT_DESCRIPTION_EN_,  DEFINITION_FR_,
        DEFINITION_EN_,         OBJECTIVE_FR_,
        OBJECTIVE_EN_,          DOMAIN_PROCESS,
        RISKS,                  CONTROL_GROUP
    )
    SELECT
        v_id_sesji,
        p.col001,   -- REFERENCE_ID
        p.col002,   -- STATUS
        p.col003,   -- CONTROL_LEVEL
        p.col004,   -- DESCRIPTION_FR_
        p.col005,   -- DESCRIPTION_EN_
        p.col006,   -- SHORT_DESCRIPTION_FR_
        p.col007,   -- SHORT_DESCRIPTION_EN_
        p.col008,   -- DEFINITION_FR_
        p.col009,   -- DEFINITION_EN_
        p.col010,   -- OBJECTIVE_FR_
        p.col011,   -- OBJECTIVE_EN_
        p.col012,   -- DOMAIN_PROCESS
        p.col013,   -- RISKS
        p.col014    -- CONTROL_GROUP
    FROM
        APEX_APPLICATION_TEMP_FILES f,
        TABLE(
            APEX_DATA_PARSER.PARSE(
                p_content       => f.blob_content,
                p_file_name     => f.filename,
                p_file_type     => APEX_DATA_PARSER.C_FILE_TYPE_XLSX,
                p_skip_rows     => 1
            )
        ) p
    WHERE f.name = :P_PLIK;

    -- Uruchom wlasciwy import z pakietu
    PKG_IMPORT_KONTROLI.WYKONAJ_IMPORT(
        p_id_sesji_importu => v_id_sesji,
        p_nazwa_pliku      => :P_PLIK,
        p_uzytkownik       => :APP_USER,
        p_id_log           => v_id_log
    );

    -- Przekaz ID logu do strony APEX (do wyswietlenia statystyk)
    :P_ID_LOG_WYNIKU := v_id_log;

EXCEPTION
    WHEN OTHERS THEN
        APEX_ERROR.ADD_ERROR(
            p_message          => 'Blad wczytywania pliku: ' || SQLERRM,
            p_display_location => APEX_ERROR.c_inline_in_notification
        );
END;

```

---

### Strona 6: DAW_WYBOR_KONTROLI
- **Tryb:** Normal
- **Uwierzytelnianie:** Page Requires Authentication

#### Region: Kontrole — "Wybierz kontrole"
- **Typ:** Interactive Report
- **Źródło SQL:**
```sql
SELECT
    APEX_ITEM.CHECKBOX2(
        p_idx                      => 1,
        p_value                    => k.ID_PK_B_KONTROLA,
        p_attributes               => 'class="cb-kontrola"',
        p_checked_values           => :P6_ZAZNACZONE_ID,
        p_checked_values_delimiter => ','
    )                        AS "WYBIERZ",
    k.ID_PK_B_KONTROLA,
    k.REFERENCE_ID           AS "Reference ID",
    k.SHORT_DESCRIPTION_FR_  AS "Nazwa",
    k.CONTROL_LEVEL          AS "Poziom",
    k.DOMAIN_PROCESS         AS "Obszar",
    k.CONTROL_GROUP          AS "Grupa",
    CASE
        WHEN EXISTS (
            SELECT 1 FROM B_AUDYT_KONTROLA ak
            WHERE  ak.ID_FK_B_AUDYT     = :P6_ID_AUDYTU
              AND  ak.ID_FK_B_KONTROLA = k.ID_PK_B_KONTROLA
        ) THEN 'TAK'
        ELSE 'NIE'
    END                      AS "W AUDYCIE"
FROM
    B_KONTROLA k
WHERE
    k.STATUS != 'Deactive'
ORDER BY
    k.REFERENCE_ID

```

#### Region: Breadcrumb
- **Typ:** Breadcrumb

#### Elementy formularza

| Nazwa | Typ | Etykieta | Kolumna | LOV |
|-------|-----|----------|---------|-----|
| P6_ID_AUDYTU | Text Field | New | — | — |
| P6_ZAZNACZONE_ID | Text Field | New | — | — |

#### Przyciski

- **USUN_Z_AUDYTU** — ? [Submit Page] **(primary)**
- **DODAJ_DO_AUDYTU** — ? [Submit Page] **(primary)**

#### Procesy

**Usun_Kontrole** (After Submit, język: PL/SQL, przycisk: USUN_Z_AUDYTU)

```plsql
/*  -- KOD PL/SQL PROCESU "Usun_Kontrole" --*/
DECLARE
    v_tab  APEX_APPLICATION_GLOBAL.VC_ARR2;
    v_err  VARCHAR2(4000);
BEGIN
    -- Sprawdz czy cos zaznaczono
    IF :P6_ZAZNACZONE_ID IS NULL OR TRIM(:P6_ZAZNACZONE_ID) = '' THEN
        APEX_ERROR.ADD_ERROR(
            p_message          => 'Zaznacz przynajmniej jedną kontrolę do usunięcia.',
            p_display_location => APEX_ERROR.c_inline_in_notification
        );
        RETURN;
    END IF;
    -- Rozdziel liste ID przecinkami i iteruj
    v_tab := APEX_UTIL.STRING_TO_TABLE(:P6_ZAZNACZONE_ID, ',');
    FOR i IN 1 .. v_tab.COUNT LOOP
        IF TRIM(v_tab(i)) IS NOT NULL THEN
            BEGIN
                -- Etap 1: Usun ankiete i oceny (BEZ COMMIT)
                PKG_ANKIETA.USUN_ANKIETE(
                    p_id_audytu   => TO_NUMBER(:P6_ID_AUDYTU),
                    p_id_kontrola => TO_NUMBER(TRIM(v_tab(i)))
                );
                -- Etap 2: Usun kontrole z audytu (COMMIT wewnatrz)
                -- Jesli status audytu != Otwarty, rzuci wyjatek
                -- i cala operacja (lacznie z USUN_ANKIETE) zostanie wycofana
                PKG_AUDYT.USUN_KONTROLE(
                    p_id_audytu   => TO_NUMBER(:P6_ID_AUDYTU),
                    p_id_kontrola => TO_NUMBER(TRIM(v_tab(i))),
                    p_uzytkownik  => :APP_USER
                );
            EXCEPTION
                WHEN OTHERS THEN
                    v_err := SQLERRM;
                    -- Pomijamy ORA-20022 (kontrola nie jest w audycie)
                    IF INSTR(v_err, 'ORA-20022') = 0 THEN
                        APEX_ERROR.ADD_ERROR(
                            p_message          => 'Błąd usuwania: ' || v_err,
                            p_display_location => APEX_ERROR.c_inline_in_notification
                        );
                        RETURN;
                    END IF;
            END;
        END IF;
    END LOOP;
    -- Wyczysc zaznaczenie po zapisie
    :P6_ZAZNACZONE_ID := NULL;
EXCEPTION
    WHEN OTHERS THEN
        v_err := SQLERRM;
        APEX_ERROR.ADD_ERROR(
            p_message          => 'Błąd podczas usuwania kontroli z audytu: ' || v_err,
            p_display_location => APEX_ERROR.c_inline_in_notification
        );
END;

```

**Dodaj_Kontrole** (After Submit, język: PL/SQL, przycisk: DODAJ_DO_AUDYTU)

```plsql
DECLARE
    v_tab  APEX_APPLICATION_GLOBAL.VC_ARR2;
    v_err  VARCHAR2(4000);
BEGIN
    -- Sprawdz czy cos zaznaczono
    IF :P6_ZAZNACZONE_ID IS NULL OR TRIM(:P6_ZAZNACZONE_ID) = '' THEN
        APEX_ERROR.ADD_ERROR(
            p_message          => 'Zaznacz przynajmniej jedną kontrolę.',
            p_display_location => APEX_ERROR.c_inline_in_notification
        );
        RETURN;
    END IF;
    -- Rozdziel liste ID przecinkami i iteruj
    v_tab := APEX_UTIL.STRING_TO_TABLE(:P6_ZAZNACZONE_ID, ',');
    FOR i IN 1 .. v_tab.COUNT LOOP
        IF TRIM(v_tab(i)) IS NOT NULL THEN
            -- Etap 1: Dodaj kontrole do audytu
            BEGIN
                PKG_AUDYT.DODAJ_KONTROLE(
                    p_id_audytu   => TO_NUMBER(:P6_ID_AUDYTU),
                    p_id_kontrola => TO_NUMBER(TRIM(v_tab(i))),
                    p_uzytkownik  => :APP_USER
                );
            EXCEPTION
                WHEN OTHERS THEN
                    v_err := SQLERRM;
                    -- Pomijamy ORA-20012 (kontrola juz w audycie) – kontynuuj do ankiety
                    IF INSTR(v_err, 'ORA-20012') = 0 THEN
                        APEX_ERROR.ADD_ERROR(
                            p_message          => 'Błąd dodawania kontroli: ' || v_err,
                            p_display_location => APEX_ERROR.c_inline_in_notification
                        );
                        RETURN;
                    END IF;
            END;
            -- Etap 2: Wygeneruj ankiete (idempotentna – sprawdza flage)
            BEGIN
                PKG_ANKIETA.GENERUJ_ANKIETE(
                    p_id_audytu   => TO_NUMBER(:P6_ID_AUDYTU),
                    p_id_kontrola => TO_NUMBER(TRIM(v_tab(i)))
                );
            EXCEPTION
                WHEN OTHERS THEN
                    v_err := SQLERRM;
                    APEX_ERROR.ADD_ERROR(
                        p_message          => 'Błąd generowania ankiety: ' || v_err,
                        p_display_location => APEX_ERROR.c_inline_in_notification
                    );
                    RETURN;
            END;
        END IF;
    END LOOP;
    -- Wyczysc zaznaczenie po zapisie
    :P6_ZAZNACZONE_ID := NULL;
EXCEPTION
    WHEN OTHERS THEN
        v_err := SQLERRM;
        APEX_ERROR.ADD_ERROR(
            p_message          => 'Błąd podczas dodawania kontroli: ' || v_err,
            p_display_location => APEX_ERROR.c_inline_in_notification
        );
END;

```

#### Akcje dynamiczne

- **DA_Checkbox_Zmiana** — zdarzenie: Change na jQuery Selector: input.cb-kontrola
  - Krok: Execute JavaScript Code
- **DA_Po_Odswiezeniu** — zdarzenie: After Refresh na Region: Kontrole
  - Krok: Execute JavaScript Code
- **DA_Zaznacz_Wszystkie** — zdarzenie: Change na jQuery Selector: #cb-all
  - Krok: Execute JavaScript Code

#### CSS strony

```css
/* Podswietlenie zaznaczonego wiersza w IR */
#ir-kontrole tr.apex-highlighted > td {
    background-color: #e8f4fd !important;
}

/* Podswietlenie wiersza juz bedacego w audycie */
#ir-kontrole tr.juz-w-audycie > td {
    background-color: #2f5a5d !important;
}

/* Checkbox – rozmiar i wyrownanie */
#ir-kontrole input[type="checkbox"].cb-kontrola {
    width: 14px !important;
    height: 14px !important;
    cursor: pointer;
}

#ir-kontrole th input[type="checkbox"] {
    display: block;
    margin: 0 auto;
}

```

---

### Strona 10061: Help
- **Tryb:** Modal Dialog
- **Uwierzytelnianie:** Page Requires Authentication

#### Region: Search Dialog
- **Typ:** Dynamic Content

#### Elementy formularza

| Nazwa | Typ | Etykieta | Kolumna | LOV |
|-------|-----|----------|---------|-----|
| P10061_PAGE_ID | Hidden | — | — | — |

---

---

## Shared Components

### Listy wartości (LOV)

**B_AUDYT.B_AUDYT_NUMER_AUDYTU** — typ: Table / View
- Tabela: `B_AUDYT`
- Return: `ID_PK_B_AUDYT`
- Display: `B_AUDYT_NUMER_AUDYTU`

**B_KONTROLA.REFERENCE_ID** — typ: Table / View
- Tabela: `B_KONTROLA`
- Return: `ID_PK_B_KONTROLA`
- Display: `REFERENCE_ID`

**B_SL_C_PYTANIE.B_SL_C_PYTANIE_TRESC** — typ: Table / View
- Tabela: `B_SL_C_PYTANIE`
- Return: `ID_PK_B_SL_C_PYTANIE`
- Display: `B_SL_C_PYTANIE_TRESC`

**B_LISTA_KONTROLI_DO_AUDYTU** — typ: SQL Query
- Return: `ID_FK_B_KONTROLA`
- Display: `OPIS_KONTROLI`
```sql
SELECT
	DISTINCT A.ID_FK_B_KONTROLA,
	b.REFERENCE_ID || ' - ' || b.SHORT_DESCRIPTION_EN_ AS OPIS_KONTROLI
FROM
	B_ANKIETA A
LEFT JOIN B_KONTROLA b ON
	b.ID_PK_B_KONTROLA = A.ID_FK_B_KONTROLA
WHERE 
  A.ID_FK_B_AUDYT = :B_APP_ID_AUDYT 
    --OR :B_APP_ID_AUDYT IS NULL
ORDER BY b.REFERENCE_ID || ' - ' || b.SHORT_DESCRIPTION_EN_ 

```

**B_SL_C_ODPOWIEDZ** — typ: 

**ADLOV** — typ: SQL Query
- Return: `IDNAME`
```sql
SELECT * FROM TABLE(AD.query_all(:P10043_AD))
```

**DESKTOP THEME STYLES** — typ: SQL Query
- Return: `R`
- Display: `D`
```sql
select s.name d,
       s.theme_style_id r
  from apex_application_theme_styles s,
       apex_application_themes t
 where s.application_id = :app_id
   and t.application_id = s.application_id
   and t.theme_number   = s.theme_number
   and t.is_current     = 'Yes'
 order by 1

```

**USER_THEME_PREFERENCE** — typ: 

**TIMEFRAME (4 WEEKS)** — typ: SQL Query
- Return: `SECONDS`
- Display: `DISP`
```sql
select disp,
       val as seconds
  from table( apex_util.get_timeframe_lov_data )
 order by insert_order

```

**VIEW_AS_REPORT_CHART** — typ: 

**ACCESS_ROLES** — typ: SQL Query
- Return: `R`
- Display: `D`
```sql
select role_name d, role_id r
from APEX_APPL_ACL_ROLES where application_id = :APP_ID 
order by 1

```

**EMAIL_USERNAME_FORMAT** — typ: 

**FEEDBACK_RATING** — typ: 

**FEEDBACK_STATUS** — typ: 

### Schematy autoryzacji

**AD Role** — typ: PL/SQL Function Returning Boolean
```plsql
RETURN LCDT.AD.authorization_rau('Tu wpisz nazwe roli', :APP_ID, :APP_USER) > 0;
```

**Administration Rights** — typ: Is In Role or Group
- Rola: Administrator

**Reader Rights** — typ: PL/SQL Function Returning Boolean
```plsql
if nvl(apex_app_setting.get_value(
   p_name => 'ACCESS_CONTROL_SCOPE'),'x') = 'ALL_USERS' then
    -- allow user not in the ACL to access the application
    return true;
else
    -- require user to have at least one role
    return apex_acl.has_user_any_roles (
        p_application_id => :APP_ID, 
        p_user_name      => :APP_USER);
end if;

```

**Contribution Rights** — typ: Is In Role or Group
- Rola: Administrator,Contributor

### Listy nawigacyjne

**Navigation Menu**
- DAW_WYSZUKIWANIE → 3
- DAW_IMPORT_KONTROLI → 5
- DAW_LISTA_AUDYTOW → 4
- DAW_WYBOR_KONTROLI → 6
- DAW_ANKIETA → 2
- Home → 1

**Navigation Bar**
- Admin → 10000
- Install App → None
- Feedback → 10050
- About → None
- Page Help → 10061
- --- → None
- About Page → 10060
- &APP_USER. → None
- --- → None
- Sign Out → None
- Settings → 20000

**Application Configuration**
- Configuration Options → 10010

**User Interface**
- Theme Style Selection → 10020

**Activity Reports**
- Dashboard → 10030
- Top Users → 10031
- Application Error Log → 10032
- Page Performance → 10033
- Page Views → 10034
- Automations Log → 10035

**Access Control**
- Users → 10041
- Access Control → 10040

**Feedback**
- User Feedback → 10053

**User Settings**
- Push Notifications → 20010

### Zmienne globalne

| Nazwa | Zakres |
|-------|--------|
| B_APP_ID_AUDYT | Application |
| B_APP_ID_KONTROLI | Application |
| G_FIRSTNAME | Global |
| G_LASTNAME | Global |
| G_EMAIL | Global |

### Opcje budowania

- **Commented Out** — Exclude
- **Feature: Access Control** — Include
- **Feature: Activity Reporting** — Include
- **Feature: Feedback** — Include
- **Feature: Configuration Options** — Include
- **Feature: About Page** — Include
- **Feature: Theme Style Selection** — Include
- **Feature: Push Notifications** — Include
- **Feature: User Settings** — Include

### Breadcrumbs

- **Breadcrumb:** DAW_LISTA_AUDYTOW (strona 4) → DAW_WYBOR_KONTROLI (strona 6) → Home (strona 1) → Administration (strona 10000)

### Role ACL

- **Administrator** (static_id: ADMINISTRATOR)
- **Contributor** (static_id: CONTRIBUTOR)
- **Reader** (static_id: READER)
