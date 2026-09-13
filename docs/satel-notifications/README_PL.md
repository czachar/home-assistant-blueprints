# Powiadomienia SATEL i monitoring CT 106

Pakiet dla istniejącego SATEL Gateway 0.11, identyfikatora MQTT `integra_test`
i telefonu `notify.mobile_app_s24_ultra`. Gateway w CT 106 pozostaje tylko do odczytu.
Ta paczka dodaje konfigurację po stronie Home Assistant.

## Pliki do pobrania

- [Pakiet powiadomień SATEL — YAML](https://raw.githubusercontent.com/czachar/home-assistant-blueprints/main/packages/satel_notifications.yaml)
- [Konfiguracja automatyzacji Serwerowni z CT 106 — YAML](https://raw.githubusercontent.com/czachar/home-assistant-blueprints/main/examples/serwerownia_monitor_ct106.yaml)
- [Całe repozytorium — ZIP](https://github.com/czachar/home-assistant-blueprints/archive/refs/heads/main.zip)

W repozytorium pakiet znajduje się w `packages/`, konfiguracja istniejącej
automatyzacji w `examples/`, a ta instrukcja w `docs/satel-notifications/`.
Pakiet SATEL wymaga instalacji opisanej poniżej; ponowny import samego blueprintu
Serwerowni nie dodaje pakietu ani CT 106 do istniejącej automatyzacji.

## 1. Dodaj CT 106 do obecnej automatyzacji

Najkrótsza droga: w istniejącej automatyzacji **Serwerownia monitor**, w grupie
**VM / LXC / Urządzenia → Monitorowane encje**, dodaj encję **Status** urządzenia
**LXC satel-gateway (106)**. Pozostaw dotychczasowe pozycje.

W repozytorium jest też pełna konfiguracja `examples/serwerownia_monitor_ct106.yaml`, oparta na
Twojej zapisanej konfiguracji. Możesz wkleić ją w edytorze YAML tej jednej
automatyzacji. Nie zastępuj nią całego `automations.yaml` ani pliku blueprintu.
Jeśli od czasu wcześniejszego zapisu zmieniałeś ustawienia automatyzacji, dodaj
CT 106 w interfejsie zamiast podmieniać całą konfigurację.

Plik używa `binary_sensor.lxc_satel_gateway_106_status`. Jeśli encja została
ręcznie przemianowana, wybierz jej aktualny identyfikator z urządzenia CT 106.
Zachowano pięć minut zwłoki offline i normalizację statusu UPS przez
`sensor.ups_tryb_dla_monitoringu`.

Blueprint pobrany i sprawdzony na GitHubie: **Serwerownia Monitor v1.3.7**.
Pozostaje pod dotychczasową ścieżką `czachar/serwerownia_monitor_v1.yaml` w HA.

## 2. Zainstaluj powiadomienia SATEL

Skopiuj plik `packages/satel_notifications.yaml` do katalogu `packages` w
katalogu konfiguracji Home Assistant, zwykle jako
`/config/packages/satel_notifications.yaml`.

Plik jest pakietem HA, zawierającym encje pomocnicze i automatyzacje. Nie jest
blueprintem ani kartą dashboardu.

Jeśli nie masz jeszcze włączonego ładowania pakietów, dopisz do
`configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Jeżeli sekcja `homeassistant:` już istnieje, dopisz tylko `packages:` do niej.
Nie twórz drugiej sekcji o tej samej nazwie. Jeżeli pakiety są już ładowane
przez `!include_dir_named`, wystarczy skopiowanie pliku do właściwego katalogu.
Jeśli używasz `!include_dir_merge_named`, ten format wymaga dodatkowego klucza
`satel_notifications:` nad zawartością pliku i wcięcia całej zawartości o dwie spacje.

Uruchom sprawdzenie konfiguracji w **Narzędziach deweloperskich → YAML**.
Po poprawnym wyniku uruchom ponownie Home Assistant, aby wczytać cały pakiet.

Pakiet używa encji:

- `sensor.satel_powiadomienia_pamiec` — ostatnie potwierdzone aktywne przyczyny;
- `binary_sensor.satel_powiadomienia_lacznosc` — dostępność danych gatewaya;
- `input_boolean.satel_powiadomienia_gotowe` — wewnętrzna gotowość po rozruchu;
- `input_boolean.satel_powiadomienia_awaria_lacznosci` — pamięć zgłoszonej utraty łączności.

Przy pierwszym uruchomieniu, po około 10 sekundach przygotowania, pakiet zgłasza
zastane aktywne przyczyny w jednym podsumowaniu, również problemy aktywne przed
instalacją pakietu. Po zwykłym restarcie odtworzona pamięć
zapobiega ponownemu zgłaszaniu niezmienionych przyczyn. Nie zmieniaj ręcznie
wewnętrznych pomocników ani identyfikatorów encji pakietu.

## Zakres powiadomień

Stan CT 106 obsługuje istniejąca automatyzacja serwerowni. Pakiet SATEL obsługuje
dane alarmowe centrali oraz dostępność danych gatewaya niezależnie od stanu kontenera.
Encje SATEL są wybierane na podstawie oznaczeń publikowanych przez gateway;
nie trzeba wpisywać osobno każdego nowo wykrytego wejścia.

Wiadomości są wysyłane na `notify.mobile_app_s24_ultra`. Równocześnie aktualizowane
są dwa trwałe powiadomienia w HA: ostatnia zmiana alarmów i stan łączności. Treść
PUSH zawiera do 12 nowych i do 12 ustępujących przyczyn; pełne ostatnie potwierdzone
stany są w atrybucie `active` sensora pamięci. Błąd usługi telefonu nie blokuje
utworzonego wcześniej komunikatu w HA.

Ogólna flaga awarii systemu jest śledzona niezależnie od listy szczegółów.
Może więc wystąpić obok konkretnej awarii akumulatora. Wynik zero dla części
diagnostyki 1/4 nie kasuje aktywnej ogólnej flagi awarii.

Alarm łączności pojawia się po 60 sekundach braku wszystkich dostępnych stanów
binarnych. Po utracie pakietów może wcześniej upłynąć czas ważności MQTT;
dodatkowy nadzór co 15 sekund zabezpiecza obsługę po przeładowaniu. Powrót oznacza
ponowne pojawienie się danych, a nie kompletność każdego odczytu czy brak alarmów.

Szczegółowe awarie pochodzą z bieżącej listy `active` i są rozróżniane po
identyfikatorach. Zmiana dwóch awarii na dwie inne jest zmianą przyczyn i podlega
powiadomieniu. Pamięć awarii centrali nie jest traktowana jak nowa bieżąca awaria.
Stan `unknown`, `unavailable`, niepełny zestaw ani usunięcie encji nie potwierdzają
ustąpienia awarii.

Gateway 0.11 rozpoznaje wybrane części diagnostyki, w tym sabotaże ekspanderów i
manipulatorów LCD, problemy ich komunikacji oraz flagi zasilania i akumulatorów.
Ten pakiet nie dodaje odczytu napięć w V ani jakości radia ABAX2 w procentach.

## Sprawdzenie po instalacji

1. Sprawdź, czy nowe encje pakietu istnieją i nie pokazują błędów szablonów.
2. Zmień bezpiecznie stan testowego wejścia alarmowego na stanowisku testowym.
   Sprawdź komunikat zawierający nazwę/identyfikator oraz informację po ustąpieniu.
   Zwykłe poruszanie się przed czujką PIR nie służy do testu alarmu strefy.
3. Do sprawdzenia łączności na stanowisku testowym zatrzymaj usługę gatewaya
   w CT 106 na ponad minutę. Kontener może przez cały czas działać. Po uruchomieniu
   usługi powinny powrócić dane, a informacja o powrocie dotyczy zakończonej awarii
   komunikacji. Nie traktuj zatrzymania gatewaya jako testu alarmu samej centrali.

## Granice działania

Pakiet nie uruchamia odczytów SATEL i nie steruje centralą. Reaguje na dane,
które docierają do HA. Nie odtworzy krótkiego zdarzenia, którego gateway lub HA
nie odebrały, ani impulsu zakończonego w początkowym, około 10-sekundowym oknie
inicjalizacji. PUSH zależy również od działania HA, usługi powiadomień, sieci i telefonu.
Pamięć stanów nie jest potwierdzeniem dostarczenia wiadomości na telefon.
Po przeładowaniu samych pomocników odzyskanie gotowości może potrwać do około
70 sekund. Do pierwszej instalacji zalecany jest pełny restart HA opisany wyżej.
Wyłączone lub usunięte źródło nie potwierdza ustąpienia jego wcześniejszego alarmu;
taki wpis pozostaje w pamięci do poprawnego odczytu `off` albo świadomego
uporządkowania konfiguracji po zmianie instalacji.

## Sprawdzenie plików przed wydaniem

Przeprowadzono lokalne parsowanie YAML i wykonanie szablonów na przykładowych
zdarzeniach: nowe/ustępujące przyczyny, zmiana dwóch awarii na dwie inne,
niedostępność i częściowy odczyt, zduplikowane źródła, zmiana nazwy, odtworzenie
pamięci, krótkie zdarzenie on/off, nowe wejścia oraz niezależna ogólna flaga awarii.
Test nie zastępuje kontroli konfiguracji i próby powiadomienia w Twoim HA.

## Źródła

- Aktualny blueprint użytkownika:
  https://github.com/czachar/home-assistant-blueprints/blob/main/blueprints/automation/serwerownia/serwerownia_monitor_v1.yaml
- Pobrany plik miał Git blob SHA `d6551b00261b060e1796819607a9bd4c3deaebb0` i nazwę wersji `Serwerownia Monitor v1.3.7`.
- Pakiety Home Assistant: https://www.home-assistant.io/docs/configuration/packages/
- Szablony wyzwalane zdarzeniami i odtwarzanie ich atrybutów:
  https://www.home-assistant.io/integrations/template/

Pliki przeszły opisane wyżej testy lokalne. Publikacja na GitHubie nie instaluje
konfiguracji w Home Assistant; instalacja i próba w HA pozostają do wykonania.
