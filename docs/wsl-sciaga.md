# WSL — ściąga (Windows 11)

---

## Start i zarządzanie WSL *(z PowerShell / cmd)*

| Komenda | Co robi |
|---|---|
| `wsl` | Uruchom domyślną dystrybucję |
| `wsl -d Ubuntu` | Uruchom konkretną dystrybucję |
| `wsl -l -v` | Lista dystrybucji + status |
| `wsl --shutdown` | Zamknij wszystkie dystrybucje |
| `wsl --update` | Zaktualizuj WSL |
| `wsl --install` | Pierwsza instalacja WSL + Ubuntu |
| `wsl --install -d Ubuntu-24.04` | Instalacja konkretnej wersji |
| `wsl --export Ubuntu C:\backup\ubuntu.tar` | Backup dystrybucji |
| `wsl --unregister Ubuntu` | **Usuwa** dystrybucję (ostrożnie!) |

---

## Codzienna praca *(w terminalu Linux)*

| Komenda | Co robi |
|---|---|
| `pwd` | Gdzie jestem (bieżący katalog) |
| `ls -la` | Lista plików ze szczegółami |
| `cd ~` | Przejdź do katalogu domowego |
| `cd /mnt/c` | Przejdź na dysk C: Windows |
| `clear` | Wyczyść ekran |
| `exit` | Wyjdź z WSL |
| `mkdir nazwa` | Utwórz katalog |
| `touch plik.txt` | Utwórz pusty plik |
| `cp -r src dst` | Kopiuj (katalog: `-r`) |
| `mv stary nowy` | Przenieś / zmień nazwę |
| `rm -r katalog` | Usuń plik lub katalog |
| `nano plik.txt` | Edytuj plik (łatwy edytor) |
| `cat plik.txt` | Wyświetl zawartość pliku |
| `grep -R "tekst" .` | Szukaj tekstu w plikach |
| `find . -name "*.py"` | Znajdź pliki po wzorcu nazwy |

---

## Uprawnienia i procesy

| Komenda | Co robi |
|---|---|
| `whoami` | Nazwa bieżącego użytkownika |
| `sudo polecenie` | Wykonaj jako administrator |
| `passwd` | Zmień swoje hasło |
| `sudo passwd user` | Reset hasła użytkownika |
| `chmod +x skrypt.sh` | Nadaj prawa wykonywania |
| `ps aux` | Lista procesów |
| `kill -9 <PID>` | Wymuś zamknięcie procesu |
| `df -h` | Wolne miejsce na dyskach |
| `du -sh *` | Rozmiary podkatalogów |

---

## Sieć

| Komenda | Co robi |
|---|---|
| `ip a` | Adresy IP interfejsów |
| `ping -c 4 google.com` | Test połączenia |
| `ss -tulpen` | Porty nasłuchujące |
| `curl -I https://adres.pl` | Test HTTP |
| `wget <url>` | Pobierz plik |

---

## Integracja Windows ↔ Linux

| Komenda | Co robi |
|---|---|
| `cd /mnt/c/Users/TwojLogin` | Twój profil Windows w WSL |
| `explorer.exe .` | Otwórz bieżący katalog w Eksploratorze |
| `code .` | Otwórz VS Code w WSL (wymaga rozszerzenia WSL) |
| `\\wsl$\Ubuntu\home\user` | Linuxowe pliki dostępne z Windows (wklej do paska adresu) |

---

## 5 typowych scenariuszy

### 1. Instalacja WSL od zera
```
# PowerShell (Administrator)
wsl --install
# po restarcie → podaj nazwę użytkownika i hasło
# na koniec:
sudo apt update && sudo apt upgrade -y
```

### 2. Reset zapomnianego hasła
```
# PowerShell
wsl -d Ubuntu -u root
# w WSL jako root:
passwd twoj_uzytkownik
exit
```

### 3. Klonowanie repo Git i praca
```
cd ~
mkdir projekty && cd projekty
git clone https://github.com/uzytkownik/repo.git
cd repo
code .
```

### 4. Python — środowisko wirtualne
```
sudo apt install python3 python3-venv python3-pip -y
cd ~/projekty/repo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Backup dystrybucji i przywracanie
```
# PowerShell — backup
wsl --export Ubuntu C:\WSL_Backup\ubuntu.tar

# PowerShell — przywracanie jako nowa dystrybucja
wsl --import UbuntuRestore C:\WSL\UbuntuRestore C:\WSL_Backup\ubuntu.tar
```

---

## Proxy w sieci korporacyjnej (Credit Agricole)

W sieci CA cały ruch do internetu przechodzi przez proxy. WSL domyślnie
o tym nie wie — trzeba skonfigurować ręcznie.

**Dane proxy:**

| Parametr | Wartość |
|---|---|
| Proxy główne | `proxy.creditagricole:8080` |
| Proxy zapasowe | `proxy2.creditagricole:8080` |
| Proxy aplikacyjne | `pxapp.creditagricole:8080` / `pxapp2.creditagricole:8080` |

### Krok 1 — DNS (jednorazowo)

```bash
sudo bash -c 'cat > /etc/wsl.conf << EOF
[network]
generateResolvConf = false

[interop]
appendWindowsPath = true
EOF'
```

Potem ustaw firmowy DNS:
```bash
sudo rm /etc/resolv.conf
sudo bash -c 'cat > /etc/resolv.conf << EOF
nameserver 172.16.131.20
search grupa.lukas creditagricole
EOF'
```

Zrestartuj WSL (`wsl --shutdown` z PowerShell) i wejdź ponownie.

Sprawdź, czy DNS działa:
```bash
nslookup proxy2.creditagricole
```

### Krok 2 — Zmienne środowiskowe (proxy systemowe)

```bash
sudo nano /etc/environment
```

Dodaj:
```bash
http_proxy="http://login:haslo@proxy2.creditagricole:8080"
https_proxy="http://login:haslo@proxy2.creditagricole:8080"
ftp_proxy="http://login:haslo@proxy2.creditagricole:8080"
HTTP_PROXY="http://login:haslo@proxy2.creditagricole:8080"
HTTPS_PROXY="http://login:haslo@proxy2.creditagricole:8080"
no_proxy="localhost,127.0.0.1,.creditagricole,.grupa.lukas,.lukas,.efl.com.pl,.eflservice.pl,.catest,.ca-test.pl,.ca-ubezpieczenia,.local,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
NO_PROXY="localhost,127.0.0.1,.creditagricole,.grupa.lukas,.lukas,.efl.com.pl,.eflservice.pl,.catest,.ca-test.pl,.ca-ubezpieczenia,.local,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
```

> Znaki specjalne w haśle trzeba URL-enkodować (np. `@` → `%40`, `#` → `%23`, `!` → `%21`).

Zapisz i **zrestartuj WSL** (`wsl --shutdown`).

### Krok 3 — APT (apt update / apt install)

```bash
sudo nano /etc/apt/apt.conf.d/99proxy.conf
```

Wpisz:
```
Acquire::http::Proxy "http://login:haslo@proxy2.creditagricole:8080";
Acquire::https::Proxy "http://login:haslo@proxy2.creditagricole:8080";
```

Test:
```bash
sudo apt update
```

### Krok 4 — GIT

```bash
git config --global http.proxy http://login:haslo@proxy2.creditagricole:8080
git config --global https.proxy http://login:haslo@proxy2.creditagricole:8080
```

Wyłączenie proxy (np. w domu):
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### Krok 5 — PIP (Python)

```bash
mkdir -p ~/.config/pip
nano ~/.config/pip/pip.conf
```

Wpisz:
```ini
[global]
proxy = http://login:haslo@proxy2.creditagricole:8080
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
```

Lub jednorazowo z linii komend:
```bash
pip install --proxy http://login:haslo@proxy2.creditagricole:8080 \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org <pakiet>
```

### Krok 6 — CURL i WGET

CURL — utwórz plik `~/.curlrc`:
```bash
nano ~/.curlrc
```
```
proxy = login:haslo@proxy2.creditagricole:8080
```

WGET — utwórz plik `~/.wgetrc`:
```bash
nano ~/.wgetrc
```
```
use_proxy = on
http_proxy = http://login:haslo@proxy2.creditagricole:8080
https_proxy = http://login:haslo@proxy2.creditagricole:8080
```

### Krok 7 — NPM / Node.js (opcjonalnie)

```bash
npm config set proxy http://login:haslo@proxy2.creditagricole:8080
npm config set https-proxy http://login:haslo@proxy2.creditagricole:8080
```

### Test połączenia — sprawdź po kolei

```bash
curl -v https://www.google.com          # HTTP przez proxy
wget -q -O /dev/null https://google.com # WGET
sudo apt update                          # APT
pip install --dry-run requests           # PIP (bez instalacji)
git ls-remote https://github.com/git/git # GIT
```

### Domeny lokalne (bez proxy — połączenie DIRECT)

Poniższe domeny **nie wymagają proxy** — ruch idzie bezpośrednio:

```
.creditagricole    .grupa.lukas    .lukas
.efl.com.pl        .eflservice.pl  .catest
.ca-test.pl        .ca-ubezpieczenia  .local
localhost          127.0.0.1
10.0.0.0/8         172.16.0.0/12   192.168.0.0/16
```

### Częste problemy z proxy

| Problem | Rozwiązanie |
|---|---|
| `407 Proxy Authentication Required` | Dodaj login i hasło do URL proxy |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Dodaj `trusted-host` (pip) lub `--no-check-certificate` (wget) |
| Znaki specjalne w haśle | URL-encode: `@`→`%40` `#`→`%23` `!`→`%21` `$`→`%24` |
| Nie działa po restarcie | Sprawdź, czy `/etc/resolv.conf` się nie nadpisał — patrz Krok 1 |
| W domu nie łączy | Wyłącz proxy: `unset http_proxy https_proxy` lub zakomentuj w plikach |

---

## Gdy coś nie działa

1. Zamknij i uruchom ponownie WSL:
   `wsl --shutdown` → odczekaj chwilę → `wsl`
2. Sprawdź wersję dystrybucji: `lsb_release -a`
3. Sprawdź kernel: `uname -a`
4. Zaktualizuj WSL: `wsl --update` *(z PowerShell)*
5. Ostateczność — odtwórz ze zrobionego wcześniej backupu.

---

*WSL ściąga · marzec 2026*
