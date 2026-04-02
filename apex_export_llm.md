APP:338|START338141|SKW_2_APEX (Working Copy: tr_20260318)
===PAGE:1|Home|Normal|auth:required
RGN:My Info|Static Content
RGN:Copyright|Static Content
RGN:Tytuł|title:SKW_2_APEX by DAW|Static Content
===PAGE:2|DAW_ANKIETA|Normal|auth:required
CSS:inline
.tekst-zawijany {
    white-space: pre-wrap !important;
    min-width: 150px; /* Opcjonalnie: minimalna szerokość kolumny */
}

---
RGN:Przerywnik|Static Content
RGN:P2_SKUTECZNOSC_OCENA|Interactive Grid|src:SQL|edit:true|ops:Update
```sql
SELECT * FROM B_OCENA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = 2 /*skuteczność*/

```
COL:B_OCENA_PRZELAMANA_UZASADNIENIE|Textarea|heading:Przełamanie - komentarz
COL:B_OCENA_CZY_NADPISANA|Switch|heading:Czy przełamanie?
COL:B_OCENA_NADPISANA|Number Field|heading:Ocena nadpisana:
COL:B_OCENA_LICZONA|Number Field|heading:Ocena wyliczona:
COL:ID_PK_B_OCENA|Hidden|pk:true
COL:B_SL_C_PYTANIE_DZIEDZINA_ID|Hidden
COL:ID_FK_B_KONTROLA|Hidden
COL:ID_FK_B_AUDYT|Hidden
COL:APEX$ROW_ACTION|Actions Menu
COL:APEX$ROW_SELECTOR|Row Selector
RGN:Przerywnik|Static Content
RGN:P2_SKUTECZNOSC|title:Adekwatność|Interactive Grid|src:SQL|edit:true|ops:Update,Delete
```sql
SELECT * FROM B_ANKIETA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = 2 /*Skuteczność*/

```
COL:ID_PK_B_ANKIETA|Hidden|pk:true
COL:ID_FK_B_AUDYT|Hidden
COL:ID_FK_B_KONTROLA|Hidden
COL:ID_FK_B_SL_C_PYTANIE|Hidden
COL:B_SL_C_PYTANIE_WAGA|Hidden
COL:ID_FK_B_SL_C_PYTANIE_DZIEDZINA|Hidden
COL:SHORT_DESCRIPTION_FR_|Hidden
COL:REFERENCE_ID|Hidden
COL:B_ANKIETA_ODPOWIEDZ|Select List|heading:Odpowiedź|lov:B_SL_C_ODPOWIEDZ
COL:B_ANKIETA_OCENA_WAZONA_LICZ|Number Field|heading:Ocena ważona
COL:B_ANKIETA_KOMENTARZ|Textarea|heading:Komentarz
COL:B_ANKIETA_LINK_DOKUMENTACJA|Textarea|heading:Link do dokumentacji
COL:APEX$ROW_ACTION|Actions Menu
COL:APEX$ROW_SELECTOR|Row Selector
COL:DATA_OSTATNIEJ_KONTROLI_NA_MOMENT_AUDYTU|Date Picker|heading:Data Ostatniej Kontroli Na Moment Audytu
COL:PYTANIE_TEKST|Display Only|heading:Pytanie
COL:PYTANIE_KOLEJNOSC|Display Only
RGN:P2_ADEKWATNOSC_OCENA|Interactive Grid|src:SQL|edit:true|ops:Update
```sql
SELECT * FROM B_OCENA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = 1 /*ADEKWATNOŚĆ*/

```
COL:ID_FK_B_AUDYT|Hidden
COL:ID_FK_B_KONTROLA|Hidden
COL:B_SL_C_PYTANIE_DZIEDZINA_ID|Hidden
COL:ID_PK_B_OCENA|Hidden|pk:true
COL:B_OCENA_LICZONA|Number Field|heading:Ocena wyliczona:
COL:B_OCENA_NADPISANA|Number Field|heading:Ocena nadpisana:
COL:APEX$ROW_ACTION|Actions Menu
COL:APEX$ROW_SELECTOR|Row Selector
COL:B_OCENA_CZY_NADPISANA|Switch|heading:Czy przełamanie?
COL:B_OCENA_PRZELAMANA_UZASADNIENIE|Textarea|heading:Przełamanie - komentarz
RGN:P2_ADEKWATNOSC|title:Adekwatność|Interactive Grid|src:SQL|edit:true|ops:Update,Delete
```sql
SELECT * FROM B_ANKIETA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = 1 /*ADEKWATNOŚĆ*/

```
COL:APEX$ROW_SELECTOR|Row Selector
COL:APEX$ROW_ACTION|Actions Menu
COL:PYTANIE_TEKST|Display Only|heading:Pytanie
COL:ID_PK_B_ANKIETA|Hidden|pk:true
COL:ID_FK_B_AUDYT|Hidden
COL:ID_FK_B_KONTROLA|Hidden
COL:ID_FK_B_SL_C_PYTANIE|Hidden
COL:B_SL_C_PYTANIE_WAGA|Hidden
COL:ID_FK_B_SL_C_PYTANIE_DZIEDZINA|Hidden
COL:SHORT_DESCRIPTION_FR_|Hidden
COL:REFERENCE_ID|Hidden
COL:B_ANKIETA_ODPOWIEDZ|Select List|heading:Odpowiedź|lov:B_SL_C_ODPOWIEDZ
COL:B_ANKIETA_OCENA_WAZONA_LICZ|Number Field|heading:Ocena ważona
COL:B_ANKIETA_KOMENTARZ|Textarea|heading:Komentarz
COL:B_ANKIETA_LINK_DOKUMENTACJA|Textarea|heading:Link do dokumentacji
COL:DATA_OSTATNIEJ_KONTROLI_NA_MOMENT_AUDYTU|Date Picker|heading:Data Ostatniej Kontroli Na Moment Audytu
COL:PYTANIE_KOLEJNOSC|Display Only
ITEM:P2_AUDYT_ID|Select List|label:Numer Audytu|lov:B_AUDYT.B_AUDYT_NUMER_AUDYTU
ITEM:P2_KONTROLA_ID|Select List|label:Numer Kontroli|lov:B_LISTA_KONTROLI_DO_AUDYTU
BTN:WyliczOcenę|action:Submit Page|hot:true
PROC:P2_ADEKWATNOSC - DMI|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC:WyliczenieOceny - SKUTECZNOSC|Execute Code|lang:PL/SQL|point:Processing
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
PROC:P2_SKUTECZNOSC - DMI|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC:P2_SKUTECZNOSC - Save Interactive Grid Data|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC:P2_ADEKWATNOSC_OCENA - Save Interactive Grid Data|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC:WyliczenieOceny - ADEKWATNOSC|Execute Code|lang:PL/SQL|point:Processing
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
DA:Oblicz ocenę ważoną AD|event:Change|sel:Column(s)|scope:Static
DA_STEP:Set Value
DA:Ustawienie B_APP_ID_AUDYT|event:Change|sel:Item(s)|scope:Static
DA_STEP:Execute Server-side Code
```plsql
begin
  :B_APP_ID_AUDYT := :P2_AUDYT_ID;
end;

```
DA_STEP:Refresh|affects:jQuery Selector: .odswiez-mnie
DA:Ustawienie B_APP_ID_KONTROLI|event:Change|sel:Item(s)|scope:Static
DA_STEP:Execute Server-side Code
```plsql
Begin
  :B_APP_ID_KONTROLI := :P2_KONTROLA_ID;
End;

```
DA_STEP:Refresh|affects:jQuery Selector: .odswiez-mnie
DA:Oblicz ocenę ważoną SK|event:Change|sel:Column(s)|scope:Static
DA_STEP:Set Value
DA_STEP:Execute Server-side Code
```plsql
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
===PAGE:3|DAW_WYSZUKIWANIE|Normal|auth:required
RGN:Search Results|Classic Report|src:B_KONTROLA
COL:ID_PK_B_KONTROLA|Hidden
COL:REFERENCE_ID|Plain Text|heading:Reference ID
COL:DATA_OSTATNIEJ_KONTROLI|Hidden
COL:DATA_PIERWSZEJ_KONTROLI|Hidden
COL:LICZBA_WYKONANYCH_KONTROLI|Hidden
COL:STATUS|Plain Text|heading:Status
COL:CONTROL_LEVEL|Plain Text|heading:Control Level
COL:DESCRIPTION_FR_|Plain Text|heading:Description Fr
COL:DESCRIPTION_EN_|Plain Text|heading:Description En
COL:SHORT_DESCRIPTION_FR_|Plain Text|heading:Short Description Fr
COL:SHORT_DESCRIPTION_EN_|Plain Text|heading:Short Description En
COL:DEFINITION_FR_|Hidden
COL:DEFINITION_EN_|Hidden
COL:OBJECTIVE_FR_|Hidden
COL:OBJECTIVE_EN_|Hidden
COL:DOMAIN_PROCESS|Plain Text|heading:Domain Process
COL:RISKS|Plain Text|heading:Risks
COL:CONTROL_GROUP|Plain Text|heading:Control Group
RGN:Search|Smart Filters
===PAGE:4|DAW_LISTA_AUDYTOW|Normal|auth:required
RGN:Breadcrumb|Breadcrumb
RGN:filtry-kontroli|title:Filtry wyszukiwania|Static Content
RGN:ListaAudytow|Interactive Grid|src:B_AUDYT|edit:true|ops:Add,Update,Delete
COL:ID_PK_B_AUDYT|Hidden|pk:true
COL:B_AUDYT_NUMER_AUDYTU|Link|heading:B Audyt Numer Audytu|link:page6
COL:STATUS_AUDYTU|Text Field|heading:Status Audytu
COL:SZEF_MISJI_LOGIN|Text Field|heading:Szef Misji Login
COL:AUDYTORZY_LOGINY|Textarea|heading:Audytorzy Loginy
COL:DATA_UTWORZENIA|Date Picker|heading:Data Utworzenia
COL:DATA_ZAMROZENIA|Date Picker|heading:Data Zamrozenia
COL:DATA_ZAKONCZENIA|Date Picker|heading:Data Zakonczenia
COL:ZAMROZIL_LOGIN|Text Field|heading:Zamrozil Login
COL:ZAKONCZYL_LOGIN|Text Field|heading:Zakonczyl Login
COL:LiczbSprawdzanychKontroli|Display Only
COL:APEX$ROW_SELECTOR|Row Selector
COL:APEX$ROW_ACTION|Actions Menu
ITEM:P4_FILTR_REFERENCE_ID|Text Field|label:Filtr Reference Id
PROC:ListaAudytow - Save Interactive Grid Data|Interactive Grid - Automatic Row Processing (DML)|point:Processing
===PAGE:5|DAW_IMPORT_KONTROLI|Normal|auth:required
ITEM:P_ID_LOG_WYNIKU|Hidden
ITEM:P_PLIK|File Upload|label:Plik do wczytania - Excel
BTN:WczytajPlik|action:Submit Page
PROC:Wczyt|Execute Code|lang:PL/SQL|point:Before Header
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
===PAGE:6|DAW_WYBOR_KONTROLI|Normal|auth:required
CSS:inline
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

---
RGN:Kontrole|title:Wybierz kontrole|Interactive Report|src:SQL
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
RGN:Breadcrumb|Breadcrumb
ITEM:P6_ID_AUDYTU|Text Field|label:New
ITEM:P6_ZAZNACZONE_ID|Text Field|label:New
BTN:USUN_Z_AUDYTU|action:Submit Page|hot:true
BTN:DODAJ_DO_AUDYTU|action:Submit Page|hot:true
PROC:Usun_Kontrole|Execute Code|lang:PL/SQL|point:After Submit|btn:USUN_Z_AUDYTU
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
PROC:Dodaj_Kontrole|Execute Code|lang:PL/SQL|point:After Submit|btn:DODAJ_DO_AUDYTU
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
DA:DA_Checkbox_Zmiana|event:Change|sel:jQuery Selector|trigger:input.cb-kontrola|scope:Dynamic
DA_STEP:Execute JavaScript Code
DA:DA_Po_Odswiezeniu|event:After Refresh|sel:Region|trigger:Kontrole|scope:Static
DA_STEP:Execute JavaScript Code
DA:DA_Zaznacz_Wszystkie|event:Change|sel:jQuery Selector|trigger:#cb-all|scope:Static
DA_STEP:Execute JavaScript Code
===PAGE:10061|Help|Modal Dialog|auth:required
RGN:Search Dialog|Dynamic Content
ITEM:P10061_PAGE_ID|Hidden
===LOV:B_AUDYT.B_AUDYT_NUMER_AUDYTU|type:Table|tbl:B_AUDYT|ret:ID_PK_B_AUDYT|disp:B_AUDYT_NUMER_AUDYTU
===LOV:B_KONTROLA.REFERENCE_ID|type:Table|tbl:B_KONTROLA|ret:ID_PK_B_KONTROLA|disp:REFERENCE_ID
===LOV:B_SL_C_PYTANIE.B_SL_C_PYTANIE_TRESC|type:Table|tbl:B_SL_C_PYTANIE|ret:ID_PK_B_SL_C_PYTANIE|disp:B_SL_C_PYTANIE_TRESC
===LOV:B_LISTA_KONTROLI_DO_AUDYTU|type:SQL|ret:ID_FK_B_KONTROLA|disp:OPIS_KONTROLI
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
===LOV:B_SL_C_ODPOWIEDZ|type:
===LOV:ADLOV|type:SQL|ret:IDNAME
```sql
SELECT * FROM TABLE(AD.query_all(:P10043_AD))
```
===LOV:DESKTOP THEME STYLES|type:SQL|ret:R|disp:D
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
===LOV:USER_THEME_PREFERENCE|type:
===LOV:TIMEFRAME (4 WEEKS)|type:SQL|ret:SECONDS|disp:DISP
```sql
select disp,
       val as seconds
  from table( apex_util.get_timeframe_lov_data )
 order by insert_order

```
===LOV:VIEW_AS_REPORT_CHART|type:
===LOV:ACCESS_ROLES|type:SQL|ret:R|disp:D
```sql
select role_name d, role_id r
from APEX_APPL_ACL_ROLES where application_id = :APP_ID 
order by 1

```
===LOV:EMAIL_USERNAME_FORMAT|type:
===LOV:FEEDBACK_RATING|type:
===LOV:FEEDBACK_STATUS|type:
===AUTH:AD Role|type:PL/SQL Function Returning Boolean
```plsql
RETURN LCDT.AD.authorization_rau('Tu wpisz nazwe roli', :APP_ID, :APP_USER) > 0;
```
===AUTH:Administration Rights|type:Is In Role or Group|role:Administrator
===AUTH:Reader Rights|type:PL/SQL Function Returning Boolean
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
===AUTH:Contribution Rights|type:Is In Role or Group|role:Administrator,Contributor
===NAV:Navigation Menu|DAW_WYSZUKIWANIE->page:3|DAW_IMPORT_KONTROLI->page:5|DAW_LISTA_AUDYTOW->page:4|DAW_WYBOR_KONTROLI->page:6|DAW_ANKIETA->page:2|Home->page:1
===NAV:Navigation Bar|Admin->page:10000|Install App->page:None|Feedback->page:10050|About->page:None|Page Help->page:10061|---->page:None|About Page->page:10060|&APP_USER.->page:None|---->page:None|Sign Out->page:None|Settings->page:20000
===NAV:Application Configuration|Configuration Options->page:10010
===NAV:User Interface|Theme Style Selection->page:10020
===NAV:Activity Reports|Dashboard->page:10030|Top Users->page:10031|Application Error Log->page:10032|Page Performance->page:10033|Page Views->page:10034|Automations Log->page:10035
===NAV:Access Control|Users->page:10041|Access Control->page:10040
===NAV:Feedback|User Feedback->page:10053
===NAV:User Settings|Push Notifications->page:20010
===APP_ITEM:B_APP_ID_AUDYT|scope:Application
===APP_ITEM:B_APP_ID_KONTROLI|scope:Application
===APP_ITEM:G_FIRSTNAME|scope:Global
===APP_ITEM:G_LASTNAME|scope:Global
===APP_ITEM:G_EMAIL|scope:Global
===BUILD_OPT:Commented Out|status:Exclude
===BUILD_OPT:Feature: Access Control|status:Include
===BUILD_OPT:Feature: Activity Reporting|status:Include
===BUILD_OPT:Feature: Feedback|status:Include
===BUILD_OPT:Feature: Configuration Options|status:Include
===BUILD_OPT:Feature: About Page|status:Include
===BUILD_OPT:Feature: Theme Style Selection|status:Include
===BUILD_OPT:Feature: Push Notifications|status:Include
===BUILD_OPT:Feature: User Settings|status:Include
===BREADCRUMB:Breadcrumb|DAW_LISTA_AUDYTOW:page4->DAW_WYBOR_KONTROLI:page6->Home:page1->Administration:page10000
===ACL:Administrator|static_id:ADMINISTRATOR
===ACL:Contributor|static_id:CONTRIBUTOR
===ACL:Reader|static_id:READER