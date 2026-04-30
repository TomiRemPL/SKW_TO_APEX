APP:338|START338141|SKW_2_APEX (Working Copy: tr_20260318)
===PAGE:1|Home|Normal|auth:required
PAGE_ATTRS:identification.name=Home;identification.alias=HOME;identification.title=SKW_2_APEX;appearance.page-mode=Normal;appearance.page-template=Theme Default;appearance.template-options=#DEFAULT#;navigation.cursor-focus=Do not focus cursor;navigation.warn-on-unsaved-changes=True;security.authentication=Page Requires Authentication;security.deep-linking=Application Default;security.page-access-protection=Arguments Must Have Checksum;security.browser-cache=Application Default;session-management.rejoin-sessions=Application Default;advanced.enable-duplicate-page-submissions=Yes - Enable page to be re-posted;advanced.reload-on-submit=Only for Success;server-cache.caching=Disabled
RGN:My Info|Static Content
RGN_ATTRS:appearance.template=None;appearance.render-components=Above Content;customization.customizable=Not Customizable By End Users
RGN:Copyright|Static Content
RGN_ATTRS:appearance.template=None;appearance.render-components=Above Content;customization.customizable=Not Customizable By End Users
RGN:Tytuł|title:SKW_2_APEX by DAW|Static Content
RGN_ATTRS:appearance.template=Hero;appearance.template-options=#DEFAULT#;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;image.file-url=#APP_FILES#icons/app-icon-512.png;customization.customizable=Not Customizable By End Users
===PAGE:2|DAW_ANKIETA|Normal|auth:required
PAGE_ATTRS:identification.name=DAW_ANKIETA;identification.alias=DAW-ANKIETA;identification.title=DAW_ANKIETA;appearance.page-mode=Normal;appearance.page-template=Theme Default;appearance.template-options=#DEFAULT#;navigation.cursor-focus=Do not focus cursor;navigation.warn-on-unsaved-changes=True;security.authentication=Page Requires Authentication;security.deep-linking=Application Default;security.page-access-protection=Arguments Must Have Checksum;security.browser-cache=Application Default;session-management.rejoin-sessions=Application Default;advanced.enable-duplicate-page-submissions=Yes - Enable page to be re-posted;advanced.reload-on-submit=Only for Success;server-cache.caching=Disabled
CSS:inline
.tekst-zawijany {
    white-space: pre-wrap !important;
    min-width: 150px; /* Opcjonalnie: minimalna szerokość kolumny */
}

---
RGN:Przerywnik|Static Content
RGN_ATTRS:appearance.template=Blank with Attributes;appearance.template-options=#DEFAULT#;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
RGN:P2_SKUTECZNOSC_OCENA|Interactive Grid|src:SQL|edit:true|ops:Update
```sql
SELECT * FROM B_OCENA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = 2 /*skuteczność*/

```
RGN_ATTRS:appearance.template=Interactive Report;appearance.template-options=#DEFAULT#,t-IRR-region--hideHeader js-addHiddenHeadingRoleDesc;appearance.css-classes=odswiez-mnie;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
COL:B_OCENA_PRZELAMANA_UZASADNIENIE|Textarea|heading:Przełamanie - komentarz
COL_ATTRS:settings.resizable=True;settings.trim-spaces=Leading and Trailing;layout.sequence=100;layout.column-alignment=start;layout.stretch=Use Report Setting;validation.maximum-length=4000;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.hide=True
COL:B_OCENA_CZY_NADPISANA|Switch|heading:Czy przełamanie?
COL_ATTRS:settings.on-value=1;settings.on-label=TAK;settings.off-value=0;settings.off-label=NIE;layout.sequence=90;layout.column-alignment=center;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:B_OCENA_NADPISANA|Number Field|heading:Ocena nadpisana:
COL_ATTRS:settings.number-alignment=Start;settings.virtual-keyboard=Decimal;layout.sequence=80;layout.column-alignment=center;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:B_OCENA_LICZONA|Number Field|heading:Ocena wyliczona:
COL_ATTRS:settings.number-alignment=Start;settings.virtual-keyboard=Decimal;layout.sequence=70;layout.column-alignment=center;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:ID_PK_B_OCENA|Hidden|pk:true
COL_ATTRS:settings.value-protected=True;layout.sequence=60;session-state.data-type=VARCHAR2
COL:B_SL_C_PYTANIE_DZIEDZINA_ID|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=50;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_KONTROLA|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=40;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_AUDYT|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=30;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:APEX$ROW_ACTION|Actions Menu
COL_ATTRS:layout.sequence=20;configuration.build-option=Commented Out
COL:APEX$ROW_SELECTOR|Row Selector
COL_ATTRS:settings.enable-multi-select=True;settings.show-select-all=True;layout.sequence=10;configuration.build-option=Commented Out
RGN:Przerywnik|Static Content
RGN_ATTRS:appearance.template=Blank with Attributes;appearance.template-options=#DEFAULT#;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
RGN:P2_SKUTECZNOSC|title:Adekwatność|Interactive Grid|src:SQL|edit:true|ops:Update,Delete
```sql
SELECT * FROM B_ANKIETA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = 2 /*Skuteczność*/

```
RGN_ATTRS:appearance.template=Interactive Report;appearance.template-options=#DEFAULT#,t-IRR-region--hideHeader js-addHiddenHeadingRoleDesc;appearance.css-classes=odswiez-mnie;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
COL:ID_PK_B_ANKIETA|Hidden|pk:true
COL_ATTRS:settings.value-protected=True;layout.sequence=40;session-state.data-type=VARCHAR2
COL:ID_FK_B_AUDYT|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=50;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_KONTROLA|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=60;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_SL_C_PYTANIE|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=70;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:B_SL_C_PYTANIE_WAGA|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=80;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_SL_C_PYTANIE_DZIEDZINA|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=90;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:SHORT_DESCRIPTION_FR_|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=100;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:REFERENCE_ID|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=110;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:B_ANKIETA_ODPOWIEDZ|Select List|heading:Odpowiedź|lov:B_SL_C_ODPOWIEDZ
COL_ATTRS:layout.sequence=120;layout.column-alignment=center;layout.stretch=Use Report Setting;list-of-values.type=Shared Component;list-of-values.list-of-values=B_SL_C_ODPOWIEDZ;list-of-values.display-extra-values=True;list-of-values.display-null-value=True;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Use List of Values;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:B_ANKIETA_OCENA_WAZONA_LICZ|Number Field|heading:Ocena ważona
COL_ATTRS:settings.number-alignment=Start;settings.virtual-keyboard=Decimal;layout.sequence=130;layout.column-alignment=center;layout.stretch=Use Report Setting;column-filter.enabled=True;column-filter.lov-type=None
COL:B_ANKIETA_KOMENTARZ|Textarea|heading:Komentarz
COL_ATTRS:settings.resizable=True;settings.character-counter=True;settings.trim-spaces=Leading and Trailing;layout.sequence=140;layout.column-alignment=start;layout.stretch=Use Report Setting;appearance.css-classes=tekst-zawijany;validation.maximum-length=4000;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.hide=True
COL:B_ANKIETA_LINK_DOKUMENTACJA|Textarea|heading:Link do dokumentacji
COL_ATTRS:settings.resizable=True;settings.character-counter=True;settings.trim-spaces=Leading and Trailing;layout.sequence=150;layout.column-alignment=center;layout.stretch=Use Report Setting;validation.maximum-length=1000;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.hide=True
COL:APEX$ROW_ACTION|Actions Menu
COL_ATTRS:layout.sequence=20;configuration.build-option=Commented Out
COL:APEX$ROW_SELECTOR|Row Selector
COL_ATTRS:settings.enable-multi-select=True;settings.show-select-all=True;layout.sequence=10;configuration.build-option=Commented Out
COL:DATA_OSTATNIEJ_KONTROLI_NA_MOMENT_AUDYTU|Date Picker|heading:Data Ostatniej Kontroli Na Moment Audytu
COL_ATTRS:settings.display-as=Popup;settings.minimum-date=None;settings.maximum-date=None;settings.use-defaults=True;layout.sequence=160;layout.column-alignment=start;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=Distinct Column;column-filter.date-ranges=All;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:PYTANIE_TEKST|Display Only|heading:Pytanie
COL_ATTRS:settings.format=Plain Text;settings.based-on=Item Value;layout.sequence=30;layout.column-alignment=start;layout.stretch=Use Report Setting;appearance.css-classes=tekst-zawijany;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Distinct Column;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:PYTANIE_KOLEJNOSC|Display Only
COL_ATTRS:settings.format=Plain Text;settings.based-on=Item Value;layout.sequence=170;layout.column-alignment=start;layout.stretch=Use Report Setting;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.lov-type=Distinct Column;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
RGN:P2_ADEKWATNOSC_OCENA|Interactive Grid|src:SQL|edit:true|ops:Update
```sql
SELECT * FROM B_OCENA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.B_SL_C_PYTANIE_DZIEDZINA_ID = 1 /*ADEKWATNOŚĆ*/

```
RGN_ATTRS:appearance.template=Interactive Report;appearance.template-options=#DEFAULT#,t-IRR-region--hideHeader js-addHiddenHeadingRoleDesc;appearance.css-classes=odswiez-mnie;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
COL:ID_FK_B_AUDYT|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=30;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_KONTROLA|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=40;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:B_SL_C_PYTANIE_DZIEDZINA_ID|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=50;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_PK_B_OCENA|Hidden|pk:true
COL_ATTRS:settings.value-protected=True;layout.sequence=60;session-state.data-type=VARCHAR2
COL:B_OCENA_LICZONA|Number Field|heading:Ocena wyliczona:
COL_ATTRS:settings.number-alignment=Start;settings.virtual-keyboard=Decimal;layout.sequence=70;layout.column-alignment=center;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:B_OCENA_NADPISANA|Number Field|heading:Ocena nadpisana:
COL_ATTRS:settings.number-alignment=Start;settings.virtual-keyboard=Decimal;layout.sequence=80;layout.column-alignment=center;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:APEX$ROW_ACTION|Actions Menu
COL_ATTRS:layout.sequence=20;configuration.build-option=Commented Out
COL:APEX$ROW_SELECTOR|Row Selector
COL_ATTRS:settings.enable-multi-select=True;settings.show-select-all=True;layout.sequence=10;configuration.build-option=Commented Out
COL:B_OCENA_CZY_NADPISANA|Switch|heading:Czy przełamanie?
COL_ATTRS:settings.on-value=1;settings.on-label=TAK;settings.off-value=0;settings.off-label=NIE;layout.sequence=90;layout.column-alignment=center;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:B_OCENA_PRZELAMANA_UZASADNIENIE|Textarea|heading:Przełamanie - komentarz
COL_ATTRS:settings.resizable=True;settings.trim-spaces=Leading and Trailing;layout.sequence=100;layout.column-alignment=start;layout.stretch=Use Report Setting;validation.maximum-length=4000;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.hide=True
RGN:P2_ADEKWATNOSC|title:Adekwatność|Interactive Grid|src:SQL|edit:true|ops:Update,Delete
```sql
SELECT * FROM B_ANKIETA a 
WHERE 1=1
  AND (:B_APP_ID_AUDYT IS NULL OR A.ID_FK_B_AUDYT = :P2_AUDYT_ID)
  AND (:B_APP_ID_KONTROLI IS NULL OR A.ID_FK_B_KONTROLA = :P2_KONTROLA_ID)
  AND A.ID_FK_B_SL_C_PYTANIE_DZIEDZINA = 1 /*ADEKWATNOŚĆ*/

```
RGN_ATTRS:appearance.template=Interactive Report;appearance.template-options=#DEFAULT#,t-IRR-region--hideHeader js-addHiddenHeadingRoleDesc;appearance.css-classes=odswiez-mnie;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
COL:APEX$ROW_SELECTOR|Row Selector
COL_ATTRS:settings.enable-multi-select=True;settings.show-select-all=True;layout.sequence=10;configuration.build-option=Commented Out
COL:APEX$ROW_ACTION|Actions Menu
COL_ATTRS:layout.sequence=20;configuration.build-option=Commented Out
COL:PYTANIE_TEKST|Display Only|heading:Pytanie
COL_ATTRS:settings.format=Plain Text;settings.based-on=Item Value;layout.sequence=30;layout.column-alignment=start;layout.stretch=Use Report Setting;appearance.css-classes=tekst-zawijany;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Distinct Column;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:ID_PK_B_ANKIETA|Hidden|pk:true
COL_ATTRS:settings.value-protected=True;layout.sequence=40;session-state.data-type=VARCHAR2
COL:ID_FK_B_AUDYT|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=50;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_KONTROLA|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=60;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_SL_C_PYTANIE|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=70;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:B_SL_C_PYTANIE_WAGA|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=80;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:ID_FK_B_SL_C_PYTANIE_DZIEDZINA|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=90;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:SHORT_DESCRIPTION_FR_|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=100;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:REFERENCE_ID|Hidden
COL_ATTRS:settings.value-protected=True;layout.sequence=110;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2
COL:B_ANKIETA_ODPOWIEDZ|Select List|heading:Odpowiedź|lov:B_SL_C_ODPOWIEDZ
COL_ATTRS:layout.sequence=120;layout.column-alignment=center;layout.stretch=Use Report Setting;list-of-values.type=Shared Component;list-of-values.list-of-values=B_SL_C_ODPOWIEDZ;list-of-values.display-extra-values=True;list-of-values.display-null-value=True;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Use List of Values;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:B_ANKIETA_OCENA_WAZONA_LICZ|Number Field|heading:Ocena ważona
COL_ATTRS:settings.number-alignment=Start;settings.virtual-keyboard=Decimal;layout.sequence=130;layout.column-alignment=end;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=None;enable-users-to.hide=True
COL:B_ANKIETA_KOMENTARZ|Textarea|heading:Komentarz
COL_ATTRS:settings.resizable=True;settings.character-counter=True;settings.trim-spaces=Leading and Trailing;layout.sequence=140;layout.column-alignment=start;layout.stretch=Use Report Setting;appearance.css-classes=tekst-zawijany;validation.maximum-length=4000;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.hide=True
COL:B_ANKIETA_LINK_DOKUMENTACJA|Textarea|heading:Link do dokumentacji
COL_ATTRS:settings.resizable=True;settings.character-counter=True;settings.trim-spaces=Leading and Trailing;layout.sequence=150;layout.column-alignment=center;layout.stretch=Use Report Setting;validation.maximum-length=1000;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.hide=True
COL:DATA_OSTATNIEJ_KONTROLI_NA_MOMENT_AUDYTU|Date Picker|heading:Data Ostatniej Kontroli Na Moment Audytu
COL_ATTRS:settings.display-as=Popup;settings.minimum-date=None;settings.maximum-date=None;settings.use-defaults=True;layout.sequence=160;layout.column-alignment=start;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=Distinct Column;column-filter.date-ranges=All;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:PYTANIE_KOLEJNOSC|Display Only
COL_ATTRS:settings.format=Plain Text;settings.based-on=Item Value;layout.sequence=170;layout.column-alignment=start;layout.stretch=Use Report Setting;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.lov-type=Distinct Column;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
ITEM:P2_AUDYT_ID|Select List|label:Numer Audytu|lov:B_AUDYT.B_AUDYT_NUMER_AUDYTU
ITEM_ATTRS:settings.page-action-on-selection=Submit Page;settings.execute-validations=True;layout.sequence=20;layout.region=No Parent;layout.slot=BODY;layout.alignment=Left;layout.start-new-row=True;layout.column=Automatic;layout.new-column=True;layout.column-span=Automatic;layout.label-column-span=Page Template Default;appearance.template=Optional - Floating;appearance.template-options=#DEFAULT#;appearance.height=1;list-of-values.type=Shared Component;list-of-values.list-of-values=B_AUDYT.B_AUDYT_NUMER_AUDYTU;list-of-values.display-extra-values=True;advanced.warn-on-unsaved-changes=Page Default;source.used=Only when current value in session state is null;session-state.storage=Per Session (Persistent);security.session-state-protection=Unrestricted;security.store-value-encrypted-in-session-state=True;security.restricted-characters=All characters can be saved.
ITEM:P2_KONTROLA_ID|Select List|label:Numer Kontroli|lov:B_LISTA_KONTROLI_DO_AUDYTU
ITEM_ATTRS:settings.page-action-on-selection=Submit Page;settings.execute-validations=True;layout.sequence=40;layout.region=No Parent;layout.slot=BODY;layout.alignment=Left;layout.column=Automatic;layout.new-column=True;layout.column-span=Automatic;layout.label-column-span=Page Template Default;appearance.template=Optional - Floating;appearance.template-options=#DEFAULT#;appearance.height=1;list-of-values.type=Shared Component;list-of-values.list-of-values=B_LISTA_KONTROLI_DO_AUDYTU;list-of-values.display-extra-values=True;advanced.warn-on-unsaved-changes=Page Default;source.used=Only when current value in session state is null;session-state.storage=Per Session (Persistent);security.session-state-protection=Unrestricted;security.store-value-encrypted-in-session-state=True;security.restricted-characters=All characters can be saved.
BTN:WyliczOcenę|action:Submit Page|hot:true
BTN_ATTRS:layout.sequence=10;layout.region=No Parent;layout.slot=REGION_POSITION_05;layout.start-new-row=True;layout.column=6;layout.new-column=True;layout.column-span=Automatic;appearance.button-template=Text with Icon;appearance.hot=True;appearance.template-options=#DEFAULT#,t-Button--iconLeft,t-Button--hoverIconPush,t-Button--gapBottom;appearance.icon=fa-lg fa-save
PROC:P2_ADEKWATNOSC - DMI|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC_ATTRS:settings.target-type=Region Source;settings.prevent-lost-updates=True;settings.lock-row=True;settings.return-primary-key(s)-after-insert=True;execution.sequence=40;execution.point=Processing;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
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
PROC_ATTRS:execution.sequence=70;execution.point=Processing;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
PROC:P2_SKUTECZNOSC - DMI|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC_ATTRS:settings.target-type=Region Source;settings.prevent-lost-updates=True;settings.lock-row=True;settings.return-primary-key(s)-after-insert=True;execution.sequence=50;execution.point=Processing;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
PROC:P2_SKUTECZNOSC - Save Interactive Grid Data|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC_ATTRS:settings.target-type=Region Source;settings.prevent-lost-updates=True;settings.lock-row=True;settings.return-primary-key(s)-after-insert=True;execution.sequence=10;execution.point=Processing;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
PROC:P2_ADEKWATNOSC_OCENA - Save Interactive Grid Data|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC_ATTRS:settings.target-type=Region Source;settings.prevent-lost-updates=True;settings.lock-row=True;settings.return-primary-key(s)-after-insert=True;execution.sequence=30;execution.point=Processing;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
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
PROC_ATTRS:execution.sequence=60;execution.point=Processing;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
DA:Oblicz ocenę ważoną AD|event:Change|sel:Column(s)|scope:Static
DA_STEP:Set Value
DA_STEP_ATTRS:execution.sequence=10;execution.event=Oblicz ocenę ważoną AD;execution.fire-when-event-result-is=True;execution.fire-on-initialization=True;execution.stop-execution-on-error=True;execution.wait-for-result=True
DA_ATTRS:execution.sequence=40;execution.event-scope=Static;execution.type=Immediate
DA:Ustawienie B_APP_ID_AUDYT|event:Change|sel:Item(s)|scope:Static
DA_STEP:Execute Server-side Code
```plsql
begin
  :B_APP_ID_AUDYT := :P2_AUDYT_ID;
end;

```
DA_STEP_ATTRS:execution.sequence=10;execution.event=Ustawienie B_APP_ID_AUDYT;execution.fire-when-event-result-is=True;execution.fire-on-initialization=True;execution.stop-execution-on-error=True;execution.wait-for-result=True
DA_STEP:Refresh|affects:jQuery Selector: .odswiez-mnie
DA_STEP_ATTRS:execution.sequence=20;execution.event=Ustawienie B_APP_ID_AUDYT;execution.fire-when-event-result-is=True;execution.fire-on-initialization=True
DA_ATTRS:execution.sequence=10;execution.event-scope=Static;execution.type=Immediate
DA:Ustawienie B_APP_ID_KONTROLI|event:Change|sel:Item(s)|scope:Static
DA_STEP:Execute Server-side Code
```plsql
Begin
  :B_APP_ID_KONTROLI := :P2_KONTROLA_ID;
End;

```
DA_STEP_ATTRS:execution.sequence=10;execution.event=Ustawienie B_APP_ID_KONTROLI;execution.fire-when-event-result-is=True;execution.fire-on-initialization=True;execution.stop-execution-on-error=True;execution.wait-for-result=True
DA_STEP:Refresh|affects:jQuery Selector: .odswiez-mnie
DA_STEP_ATTRS:execution.sequence=20;execution.event=Ustawienie B_APP_ID_KONTROLI;execution.fire-when-event-result-is=True;execution.fire-on-initialization=True
DA_ATTRS:execution.sequence=20;execution.event-scope=Static;execution.type=Immediate
DA:Oblicz ocenę ważoną SK|event:Change|sel:Column(s)|scope:Static
DA_STEP:Set Value
DA_STEP_ATTRS:execution.sequence=10;execution.event=Oblicz ocenę ważoną SK;execution.fire-when-event-result-is=True;execution.fire-on-initialization=True;execution.stop-execution-on-error=True;execution.wait-for-result=True
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
DA_STEP_ATTRS:execution.sequence=30;execution.event=Oblicz ocenę ważoną SK;execution.fire-when-event-result-is=True;execution.stop-execution-on-error=True;execution.wait-for-result=True;configuration.build-option=Commented Out
DA_ATTRS:execution.sequence=30;execution.event-scope=Static;execution.type=Immediate
===PAGE:3|DAW_WYSZUKIWANIE|Normal|auth:required
PAGE_ATTRS:identification.name=DAW_WYSZUKIWANIE;identification.alias=DAW-WYSZUKIWANIE;identification.title=DAW_WYSZUKIWANIE;appearance.page-mode=Normal;appearance.page-template=Standard;appearance.template-options=#DEFAULT#;navigation.cursor-focus=Do not focus cursor;navigation.warn-on-unsaved-changes=True;security.authentication=Page Requires Authentication;security.deep-linking=Application Default;security.page-access-protection=Arguments Must Have Checksum;security.browser-cache=Application Default;session-management.rejoin-sessions=Application Default;advanced.enable-duplicate-page-submissions=Yes - Enable page to be re-posted;advanced.reload-on-submit=Only for Success;server-cache.caching=Disabled
RGN:Search Results|Classic Report|src:B_KONTROLA
RGN_ATTRS:order-by.type=None;appearance.template=Standard;appearance.template-options=#DEFAULT#,t-Region--noPadding,t-Region--hideHeader js-addHiddenHeadingRoleDesc,t-Region--scrollBody;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;server-cache.caching=Disabled;customization.customizable=Not Customizable By End Users
COL:ID_PK_B_KONTROLA|Hidden
COL_ATTRS:layout.sequence=0;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:REFERENCE_ID|Plain Text|heading:Reference ID
COL_ATTRS:layout.sequence=2;layout.column-alignment=center;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:DATA_OSTATNIEJ_KONTROLI|Hidden
COL_ATTRS:layout.sequence=3;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:DATA_PIERWSZEJ_KONTROLI|Hidden
COL_ATTRS:layout.sequence=4;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:LICZBA_WYKONANYCH_KONTROLI|Hidden
COL_ATTRS:layout.sequence=5;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:STATUS|Plain Text|heading:Status
COL_ATTRS:layout.sequence=6;layout.column-alignment=center;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:CONTROL_LEVEL|Plain Text|heading:Control Level
COL_ATTRS:layout.sequence=7;layout.column-alignment=center;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:DESCRIPTION_FR_|Plain Text|heading:Description Fr
COL_ATTRS:layout.sequence=8;layout.column-alignment=start;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:DESCRIPTION_EN_|Plain Text|heading:Description En
COL_ATTRS:layout.sequence=9;layout.column-alignment=start;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:SHORT_DESCRIPTION_FR_|Plain Text|heading:Short Description Fr
COL_ATTRS:layout.sequence=10;layout.column-alignment=start;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:SHORT_DESCRIPTION_EN_|Plain Text|heading:Short Description En
COL_ATTRS:layout.sequence=11;layout.column-alignment=start;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:DEFINITION_FR_|Hidden
COL_ATTRS:layout.sequence=12;sorting.default-sequence=1;sorting.direction=Ascending;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:DEFINITION_EN_|Hidden
COL_ATTRS:layout.sequence=13;sorting.default-sequence=1;sorting.direction=Ascending;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:OBJECTIVE_FR_|Hidden
COL_ATTRS:layout.sequence=14;sorting.default-sequence=1;sorting.direction=Ascending;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:OBJECTIVE_EN_|Hidden
COL_ATTRS:layout.sequence=15;sorting.default-sequence=1;sorting.direction=Ascending;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:DOMAIN_PROCESS|Plain Text|heading:Domain Process
COL_ATTRS:layout.sequence=16;layout.column-alignment=start;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:RISKS|Plain Text|heading:Risks
COL_ATTRS:layout.sequence=17;layout.column-alignment=start;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
COL:CONTROL_GROUP|Plain Text|heading:Control Group
COL_ATTRS:layout.sequence=18;layout.column-alignment=start;sorting.default-sequence=1;sorting.direction=Ascending;sorting.sortable=True;export-/-printing.include-in-export-/-print=True;ui-defaults-reference.table-owner=Parsing Schema;security.escape-special-characters=True
RGN:Search|Smart Filters
RGN_ATTRS:appearance.template=Standard;appearance.template-options=#DEFAULT#,t-Region--hideHeader js-addHiddenHeadingRoleDesc,t-Region--scrollBody;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
===PAGE:4|DAW_LISTA_AUDYTOW|Normal|auth:required
PAGE_ATTRS:identification.name=DAW_LISTA_AUDYTOW;identification.alias=DAW-LISTA-AUDYTOW;identification.title=DAW_LISTA_AUDYTOW;appearance.page-mode=Normal;appearance.page-template=Theme Default;appearance.template-options=#DEFAULT#;navigation.cursor-focus=Do not focus cursor;navigation.warn-on-unsaved-changes=True;security.authentication=Page Requires Authentication;security.deep-linking=Application Default;security.page-access-protection=Arguments Must Have Checksum;security.browser-cache=Application Default;session-management.rejoin-sessions=Application Default;advanced.enable-duplicate-page-submissions=Yes - Enable page to be re-posted;advanced.reload-on-submit=Only for Success;server-cache.caching=Disabled
RGN:Breadcrumb|Breadcrumb
RGN_ATTRS:appearance.template=Title Bar;appearance.template-options=#DEFAULT#,t-BreadcrumbRegion--useBreadcrumbTitle;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
RGN:filtry-kontroli|title:Filtry wyszukiwania|Static Content
RGN_ATTRS:appearance.template=Collapsible;appearance.template-options=#DEFAULT#,is-expanded,t-Region--scrollBody;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;advanced.static-id=filtry-kontroli;customization.customizable=Not Customizable By End Users
RGN:ListaAudytow|Interactive Grid|src:B_AUDYT|edit:true|ops:Add,Update,Delete
RGN_ATTRS:appearance.template=Interactive Report;appearance.template-options=#DEFAULT#,t-IRR-region--hideHeader js-addHiddenHeadingRoleDesc;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users;printing.page.size=A4;printing.page.orientation=Landscape;printing.page.units=Millimeters;printing.page.width=297;printing.page.height=210;printing.page.border-width=0.5;printing.page-header.font=Helvetica;printing.page-header.font-weight=Normal;printing.page-header.font-size=12;printing.page-header.alignment=center;printing.column-headings.font=Helvetica;printing.column-headings.font-weight=Bold;printing.column-headings.font-size=10;printing.column-headings.background-color=#EEEEEE;printing.page-footer.font=Helvetica;printing.page-footer.font-weight=Normal;printing.page-footer.font-size=12;printing.page-footer.alignment=center
COL:ID_PK_B_AUDYT|Hidden|pk:true
COL_ATTRS:settings.value-protected=True;layout.sequence=30;session-state.data-type=VARCHAR2
COL:B_AUDYT_NUMER_AUDYTU|Link|heading:B Audyt Numer Audytu|link:page6
COL_ATTRS:layout.sequence=40;layout.column-alignment=start;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Distinct Column;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True;security.escape-special-characters=True
COL:STATUS_AUDYTU|Text Field|heading:Status Audytu
COL_ATTRS:settings.trim-spaces=Leading and Trailing;settings.text-case=NO CHANGE;layout.sequence=50;layout.column-alignment=start;layout.stretch=Use Report Setting;validation.value-required=True;validation.maximum-length=20;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Distinct Column;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:SZEF_MISJI_LOGIN|Text Field|heading:Szef Misji Login
COL_ATTRS:settings.trim-spaces=Leading and Trailing;settings.text-case=NO CHANGE;layout.sequence=60;layout.column-alignment=start;layout.stretch=Use Report Setting;validation.maximum-length=100;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Distinct Column;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:AUDYTORZY_LOGINY|Textarea|heading:Audytorzy Loginy
COL_ATTRS:settings.resizable=True;settings.trim-spaces=Leading and Trailing;layout.sequence=70;layout.column-alignment=start;layout.stretch=Use Report Setting;validation.maximum-length=4000;default.duplicate-copies-existing-value=True;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=None;export-/-printing.include-in-export-/-print=True;enable-users-to.hide=True
COL:DATA_UTWORZENIA|Date Picker|heading:Data Utworzenia
COL_ATTRS:settings.display-as=Popup;settings.minimum-date=None;settings.maximum-date=None;settings.use-defaults=True;layout.sequence=80;layout.column-alignment=start;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=Distinct Column;column-filter.date-ranges=All;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:DATA_ZAMROZENIA|Date Picker|heading:Data Zamrozenia
COL_ATTRS:settings.display-as=Popup;settings.minimum-date=None;settings.maximum-date=None;settings.use-defaults=True;layout.sequence=90;layout.column-alignment=start;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=Distinct Column;column-filter.date-ranges=All;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:DATA_ZAKONCZENIA|Date Picker|heading:Data Zakonczenia
COL_ATTRS:settings.display-as=Popup;settings.minimum-date=None;settings.maximum-date=None;settings.use-defaults=True;layout.sequence=100;layout.column-alignment=start;layout.stretch=Use Report Setting;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.lov-type=Distinct Column;column-filter.date-ranges=All;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:ZAMROZIL_LOGIN|Text Field|heading:Zamrozil Login
COL_ATTRS:settings.trim-spaces=Leading and Trailing;settings.text-case=NO CHANGE;layout.sequence=110;layout.column-alignment=start;layout.stretch=Use Report Setting;validation.maximum-length=100;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Distinct Column;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:ZAKONCZYL_LOGIN|Text Field|heading:Zakonczyl Login
COL_ATTRS:settings.trim-spaces=Leading and Trailing;settings.text-case=NO CHANGE;layout.sequence=120;layout.column-alignment=start;layout.stretch=Use Report Setting;validation.maximum-length=100;default.duplicate-copies-existing-value=True;column-filter.enabled=True;column-filter.performance-impacting-operators=Contains,Starts With,Case Insensitive,Regular Expression;column-filter.text-case=Mixed;column-filter.lov-type=Distinct Column;column-filter.exact-match=True;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:LiczbSprawdzanychKontroli|Display Only
COL_ATTRS:settings.format=Plain Text;settings.based-on=Item Value;layout.sequence=130;layout.column-alignment=start;layout.stretch=Use Report Setting;session-state.data-type=VARCHAR2;column-filter.enabled=True;column-filter.lov-type=Distinct Column;export-/-printing.include-in-export-/-print=True;enable-users-to.sort=True;enable-users-to.control-break/aggregate=True;enable-users-to.hide=True
COL:APEX$ROW_SELECTOR|Row Selector
COL_ATTRS:settings.enable-multi-select=True;settings.show-select-all=True;layout.sequence=10
COL:APEX$ROW_ACTION|Actions Menu
COL_ATTRS:layout.sequence=20
ITEM:P4_FILTR_REFERENCE_ID|Text Field|label:Filtr Reference Id
ITEM_ATTRS:settings.subtype=Text;settings.trim-spaces=Leading and Trailing;settings.text-case=NO CHANGE;layout.sequence=10;layout.region=filtry-kontroli;layout.slot=BODY;layout.alignment=Left;layout.start-new-row=True;layout.column=Automatic;layout.new-column=True;layout.column-span=Automatic;layout.label-column-span=Page Template Default;appearance.template=Optional - Floating;appearance.template-options=#DEFAULT#;appearance.width=20;advanced.warn-on-unsaved-changes=Page Default;source.used=Only when current value in session state is null;session-state.storage=Per Session (Persistent);security.session-state-protection=Unrestricted;security.store-value-encrypted-in-session-state=True;security.restricted-characters=All characters can be saved.
PROC:ListaAudytow - Save Interactive Grid Data|Interactive Grid - Automatic Row Processing (DML)|point:Processing
PROC_ATTRS:settings.target-type=Region Source;settings.prevent-lost-updates=True;settings.lock-row=True;settings.return-primary-key(s)-after-insert=True;execution.sequence=10;execution.point=Processing;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
===PAGE:5|DAW_IMPORT_KONTROLI|Normal|auth:required
PAGE_ATTRS:identification.name=DAW_IMPORT_KONTROLI;identification.alias=DAW-IMPORT-KONTROLI;identification.title=DAW_IMPORT_KONTROLI;appearance.page-mode=Normal;appearance.page-template=Theme Default;appearance.template-options=#DEFAULT#;navigation.cursor-focus=Do not focus cursor;navigation.warn-on-unsaved-changes=True;security.authentication=Page Requires Authentication;security.deep-linking=Application Default;security.page-access-protection=Arguments Must Have Checksum;security.browser-cache=Application Default;session-management.rejoin-sessions=Application Default;advanced.enable-duplicate-page-submissions=Yes - Enable page to be re-posted;advanced.reload-on-submit=Only for Success;server-cache.caching=Disabled
ITEM:P_ID_LOG_WYNIKU|Hidden
ITEM_ATTRS:settings.value-protected=True;layout.sequence=30;layout.region=No Parent;layout.slot=BODY;advanced.warn-on-unsaved-changes=Page Default;source.used=Only when current value in session state is null;session-state.data-type=VARCHAR2;session-state.storage=Per Session (Persistent);security.session-state-protection=Unrestricted;security.store-value-encrypted-in-session-state=True;security.restricted-characters=All characters can be saved.
ITEM:P_PLIK|File Upload|label:Plik do wczytania - Excel
ITEM_ATTRS:display.display-as=Inline File Browse;display.capture-using=NONE;storage:.type=Table APEX_APPLICATION_TEMP_FILES;storage:.purge-file-at=End of Session;storage:.file-types=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;storage:.maximum-file-size=15000;layout.sequence=10;layout.region=No Parent;layout.slot=BODY;layout.alignment=Left;layout.column=Automatic;layout.new-column=True;layout.column-span=5;layout.label-column-span=Page Template Default;appearance.template=Optional - Floating;appearance.template-options=#DEFAULT#;appearance.width=30;advanced.warn-on-unsaved-changes=Page Default;source.used=Only when current value in session state is null;session-state.storage=Per Session (Persistent);security.session-state-protection=Unrestricted;security.restricted-characters=All characters can be saved.
BTN:WczytajPlik|action:Submit Page
BTN_ATTRS:layout.sequence=20;layout.region=No Parent;layout.slot=BODY;layout.start-new-row=True;layout.column=Automatic;layout.new-column=True;layout.column-span=Automatic;layout.alignment=Left center;appearance.button-template=Text with Icon;appearance.template-options=#DEFAULT#,t-Button--iconLeft;configuration.build-option=Commented Out
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
PROC_ATTRS:execution.sequence=10;execution.point=Before Header;execution.run-process=Once Per Page Visit (default);configuration.build-option=Commented Out
===PAGE:6|DAW_WYBOR_KONTROLI|Normal|auth:required
PAGE_ATTRS:identification.name=DAW_WYBOR_KONTROLI;identification.alias=DAW-WYBOR-KONTROLI;identification.title=DAW_WYBOR_KONTROLI;appearance.page-mode=Normal;appearance.page-template=Theme Default;appearance.template-options=#DEFAULT#;navigation.cursor-focus=Do not focus cursor;navigation.warn-on-unsaved-changes=True;security.authentication=Page Requires Authentication;security.deep-linking=Application Default;security.page-access-protection=Arguments Must Have Checksum;security.browser-cache=Application Default;session-management.rejoin-sessions=Application Default;advanced.enable-duplicate-page-submissions=Yes - Enable page to be re-posted;advanced.reload-on-submit=Only for Success;server-cache.caching=Disabled
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
RGN_ATTRS:appearance.template=Interactive Report;appearance.template-options=#DEFAULT#,t-IRR-region--hideHeader js-addHiddenHeadingRoleDesc;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;advanced.static-id=ir-kontrole;server-cache.caching=Disabled;customization.customizable=Not Customizable By End Users
RGN:Breadcrumb|Breadcrumb
RGN_ATTRS:appearance.template=Title Bar;appearance.template-options=#DEFAULT#,t-BreadcrumbRegion--useBreadcrumbTitle;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;customization.customizable=Not Customizable By End Users
ITEM:P6_ID_AUDYTU|Text Field|label:New
ITEM_ATTRS:settings.subtype=Text;settings.trim-spaces=Leading and Trailing;settings.text-case=NO CHANGE;layout.sequence=30;layout.region=No Parent;layout.slot=BODY;layout.alignment=Left;layout.start-new-row=True;layout.column=Automatic;layout.new-column=True;layout.column-span=Automatic;layout.label-column-span=Page Template Default;appearance.template=Optional - Floating;appearance.template-options=#DEFAULT#;appearance.width=30;advanced.warn-on-unsaved-changes=Page Default;source.used=Only when current value in session state is null;session-state.storage=Per Session (Persistent);security.session-state-protection=Unrestricted;security.store-value-encrypted-in-session-state=True;security.restricted-characters=All characters can be saved.
ITEM:P6_ZAZNACZONE_ID|Text Field|label:New
ITEM_ATTRS:settings.subtype=Text;settings.trim-spaces=Leading and Trailing;settings.text-case=NO CHANGE;layout.sequence=40;layout.region=No Parent;layout.slot=BODY;layout.alignment=Left;layout.start-new-row=True;layout.column=Automatic;layout.new-column=True;layout.column-span=Automatic;layout.label-column-span=Page Template Default;appearance.template=Optional - Floating;appearance.template-options=#DEFAULT#;appearance.width=30;advanced.warn-on-unsaved-changes=Page Default;source.used=Only when current value in session state is null;session-state.storage=Per Session (Persistent);security.session-state-protection=Unrestricted;security.restricted-characters=All characters can be saved.
BTN:USUN_Z_AUDYTU|action:Submit Page|hot:true
BTN_ATTRS:layout.sequence=20;layout.region=No Parent;layout.slot=BODY;layout.column=Automatic;layout.new-column=True;layout.column-span=Automatic;layout.alignment=Left center;appearance.button-template=Text;appearance.hot=True;appearance.template-options=#DEFAULT#;appearance.css-classes=t-Button--danger
BTN:DODAJ_DO_AUDYTU|action:Submit Page|hot:true
BTN_ATTRS:layout.sequence=10;layout.region=No Parent;layout.slot=BODY;layout.start-new-row=True;layout.column=Automatic;layout.new-column=True;layout.column-span=Automatic;layout.alignment=Left center;appearance.button-template=Text;appearance.hot=True;appearance.template-options=#DEFAULT#
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
PROC_ATTRS:execution.sequence=20;execution.point=After Submit;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
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
PROC_ATTRS:execution.sequence=10;execution.point=After Submit;execution.run-process=Once Per Page Visit (default);error.display-location=Inline in Notification
DA:DA_Checkbox_Zmiana|event:Change|sel:jQuery Selector|trigger:input.cb-kontrola|scope:Dynamic
DA_STEP:Execute JavaScript Code
DA_STEP_ATTRS:execution.sequence=10;execution.event=DA_Checkbox_Zmiana;execution.fire-when-event-result-is=True
DA_ATTRS:execution.sequence=10;execution.event-scope=Dynamic;execution.static-container-(jquery-selector)=#ir-kontrole;execution.type=Immediate
DA:DA_Po_Odswiezeniu|event:After Refresh|sel:Region|trigger:Kontrole|scope:Static
DA_STEP:Execute JavaScript Code
DA_STEP_ATTRS:execution.sequence=10;execution.event=DA_Po_Odswiezeniu;execution.fire-when-event-result-is=True;execution.fire-on-initialization=True
DA_ATTRS:execution.sequence=20;execution.event-scope=Static;execution.type=Immediate
DA:DA_Zaznacz_Wszystkie|event:Change|sel:jQuery Selector|trigger:#cb-all|scope:Static
DA_STEP:Execute JavaScript Code
DA_STEP_ATTRS:execution.sequence=10;execution.event=DA_Zaznacz_Wszystkie;execution.fire-when-event-result-is=True
DA_ATTRS:execution.sequence=30;execution.event-scope=Static;execution.type=Immediate
===PAGE:10061|Help|Modal Dialog|auth:required
PAGE_ATTRS:identification.name=Help;identification.alias=PAGE_HELP;identification.title=Help;appearance.page-mode=Modal Dialog;appearance.dialog-template=Theme Default;appearance.template-options=#DEFAULT#;navigation.cursor-focus=Do not focus cursor;security.authentication=Page Requires Authentication;security.deep-linking=Application Default;security.page-access-protection=Arguments Must Have Checksum;security.browser-cache=Application Default;session-management.rejoin-sessions=Application Default;advanced.enable-duplicate-page-submissions=Yes - Enable page to be re-posted;advanced.reload-on-submit=Only for Success;server-cache.caching=Disabled;configuration.build-option=Feature: About Page
RGN:Search Dialog|Dynamic Content
RGN_ATTRS:appearance.template=Blank with Attributes;appearance.template-options=#DEFAULT#;appearance.render-components=Above Content;accessibility.use-landmark=True;accessibility.landmark-type=Template Default;server-cache.caching=Disabled;customization.customizable=Not Customizable By End Users
ITEM:P10061_PAGE_ID|Hidden
ITEM_ATTRS:settings.value-protected=True;layout.sequence=10;layout.region=Search Dialog;layout.slot=BODY;advanced.warn-on-unsaved-changes=Page Default;source.used=Only when current value in session state is null;session-state.data-type=VARCHAR2;session-state.storage=Per Session (Persistent);security.session-state-protection=Checksum Required - Session Level;security.store-value-encrypted-in-session-state=True;security.restricted-characters=All characters can be saved.
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