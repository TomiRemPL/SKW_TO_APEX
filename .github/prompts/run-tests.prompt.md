---
mode: agent
description: 'Uruchamia testy pytest i raportuje wyniki. Użyj przed commitem lub po zmianach w kodzie.'
---

Uruchom testy projektu i podaj zwięzły raport.

```bash
python -m pytest tests/ -v --tb=short
```

Jeśli są błędy:
1. Podaj które testy nie przeszły
2. Wyjaśnij krótko przyczynę każdego błędu
3. Zaproponuj fix (jeśli oczywisty)

Jeśli wszystko przeszło — potwierdź jednym zdaniem.
