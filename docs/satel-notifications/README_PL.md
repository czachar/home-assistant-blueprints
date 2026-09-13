# SATEL — blueprinty powiadomień

Dwa blueprinty dla SATEL Gateway 0.11 i nowszych wersji zachowujących te same
atrybuty encji. Automatyzacje konfigurujesz w formularzach Home Assistant.
Wspólna baza pamięci jest instalowana raz. Wymagany Home Assistant 2025.10.0 lub nowszy.

| Blueprint | Działanie | Import |
|---|---|---|
| Alarmy i awarie | Alarmy wejść/stref, sabotaże, dym/zalanie i zmiany szczegółowych awarii | [Importuj do HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fczachar%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fsatel%2Fsatel_alarm_notifications.yaml) |
| Utrata i powrót danych | Brak stanów SATEL, jeden komunikat po powrocie danych | [Importuj do HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fczachar%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fsatel%2Fsatel_connectivity_notifications.yaml) |
| Serwerownia Monitor 1.3.7 | Istniejący monitoring serwerów, UPS i zasobów; tutaj dodajesz CT 106 | [Importuj do HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fczachar%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fserwerownia%2Fserwerownia_monitor_v1.yaml) |

Link importu otwiera Twoją instancję HA przez My Home Assistant. Jeśli nie działa,
wejdź do **Ustawienia → Automatyzacje i sceny → Blueprinty → Importuj blueprint**
i wklej adres odpowiedniego pliku:

- [Alarmy i awarie — GitHub](https://github.com/czachar/home-assistant-blueprints/blob/main/blueprints/automation/satel/satel_alarm_notifications.yaml)
- [Utrata i powrót danych — GitHub](https://github.com/czachar/home-assistant-blueprints/blob/main/blueprints/automation/satel/satel_connectivity_notifications.yaml)

## 1. Jednorazowa instalacja bazy pamięci

Blueprint automatyzacji tworzy automatyzację, ale nie tworzy dodatkowych
sensorów szablonowych ani pomocników. Dlatego pamięć ostatnich potwierdzonych
alarmów, sensor łączności i przygotowanie po restarcie pozostają w bazie YAML.
Baza sama nie wysyła powiadomień.

Pobierz [satel_notifications_base.yaml](https://raw.githubusercontent.com/czachar/home-assistant-blueprints/main/packages/satel_notifications_base.yaml) i zapisz jego zawartość jako:

```text
/config/packages/satel_notifications.yaml
```

**Jeśli masz poprzedni pełny pakiet `satel_notifications.yaml`, zastąp jego
zawartość bazą. Nie instaluj obu plików równocześnie.** Zachowano identyfikatory
encji, unique_id i strukturę pamięci, aby wykorzystać zapisane wcześniej stany.
Kopię poprzedniego pliku przechowuj poza katalogiem `packages`, żeby HA jej nie ładował.
Nie kopiuj całego katalogu `packages` z repozytorium — zawiera oba warianty.

Jeżeli pakiety nie są jeszcze włączone, w `configuration.yaml` dodaj:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Jeśli sekcja `homeassistant:` istnieje, dopisz tylko `packages:` do niej. Przy
istniejącym `!include_dir_named` użyj już skonfigurowanego katalogu. Wariant
`!include_dir_merge_named` wymaga dodatkowego klucza `satel_notifications:`
nad zawartością pliku oraz wcięcia całej zawartości o dwie spacje.

Uruchom **Narzędzia deweloperskie → YAML → Sprawdź konfigurację**, a następnie
pełny restart Home Assistant. Powinny pojawić się:

- `sensor.satel_powiadomienia_pamiec`;
- `binary_sensor.satel_powiadomienia_lacznosc`;
- `input_boolean.satel_powiadomienia_gotowe`;
- `input_boolean.satel_powiadomienia_awaria_lacznosci`.

Baza obsługuje jeden gateway, domyślnie `integra_test`. Dla innego identyfikatora
zmień wszystkie wystąpienia `integra_test` w bazie i ustaw ten sam identyfikator
w blueprintcie łączności. Nie kopiuj bazy pod kolejną nazwą dla drugiej centrali:
identyfikatory pomocników musiałyby być inne. Nie przełączaj istniejącej pamięci
między centralami — zawiera potwierdzone alarmy poprzedniego źródła.

## 2. Utwórz dwie automatyzacje z blueprintów

Zaimportuj oba blueprinty z tabeli powyżej. Przy każdym wybierz **Utwórz
automatyzację**, sprawdź wartości i zapisz:

1. **SATEL — alarmy i awarie**: wybierz sensor pamięci i pomocnik gotowości
   z bazy. Domyślne wartości pasują do Twojej instalacji.
2. **SATEL — utrata i powrót danych**: wybierz sensor łączności, pomocnik
   gotowości i pomocnik zgłoszonego braku danych. Gateway ID pozostaw `integra_test`.

Oba formularze umożliwiają włączenie/wyłączenie trwałych powiadomień w HA,
PUSH i informacji o ustąpieniu/powrocie. W sekcji działań telefonu jest gotowa
usługa **`notify.mobile_app_s24_ultra`**. Możesz wybrać inną usługę powiadomień
lub dodać kilku odbiorców, zachowując szablony:

```yaml
title: "{{ notification_title }}"
message: "{{ notification_message }}"
```

Sekcja działań służy wyłącznie wysyłce przygotowanej wiadomości. Nie dodawaj tam
wielominutowych opóźnień ani oczekiwania na stan — utrudnia to kolejkowanie kolejnych
alarmów i aktualizację pamięci łączności. Jeżeli dodajesz kilku odbiorców, ustaw
kontynuowanie po błędzie dla każdej akcji, aby błąd pierwszego nie pominął następnych.

Utwórz **jedną instancję każdego blueprintu dla tej bazy**. Pozostaw tylko
wbudowaną w bazę automatyzację przygotowania oraz dwie nowe automatyzacje wysyłki.
Stare automatyzacje wysyłki z pełnego pakietu nie mogą działać równolegle,
ponieważ powodowałoby to zdublowane wiadomości.

Jeśli baza działała już przed utworzeniem nowych automatyzacji, zastane alarmy
są zapisane w pamięci. Sam import blueprintu nie wysyła ich ponownie jako nowych.
Kolejne zmiany przyczyn są zgłaszane normalnie. Ręczne **Uruchom akcje** nie jest
testem zdarzenia alarmowego — do jego obsługi potrzebne są poprzedni i nowy stan.

## 3. Dodaj CT 106 w istniejącym blueprintcie Serwerowni

Serwerownia już korzysta z blueprintu **Serwerownia Monitor v1.3.7**. Otwórz
istniejącą automatyzację i w **VM / LXC / Urządzenia → Monitorowane encje** dodaj
`binary_sensor.lxc_satel_gateway_106_status`, zachowując pozostałe pozycje.
Nie twórz drugiej automatyzacji dla całej serwerowni.

[Gotowa konfiguracja istniejącej automatyzacji z CT 106](https://github.com/czachar/home-assistant-blueprints/blob/main/examples/serwerownia_monitor_ct106.yaml)
pozostaje dostępna jako przykład. To konfiguracja jednej automatyzacji korzystającej
z blueprintu, a nie osobny blueprint ani cały plik `automations.yaml`.

## Zachowanie i zakres

- Nowo wykryte wejścia są uwzględniane automatycznie dzięki oznaczeniom
  `satel_gateway`, `satel_kind`, `satel_id` i `satel_field`.
- Zgłaszane są alarmy/sabotaże oraz naruszenia o klasie `smoke` lub `moisture`.
  Zwykły ruch PIR, otwarcie drzwi, blokady, pamięci alarmów i wyjścia nie wysyłają
  alarmowego PUSH tylko dlatego, że zmieniły stan.
- Szczegółowe awarie są porównywane po identyfikatorach. Zmiana A na B wywołuje
  powiadomienie także wtedy, gdy liczba awarii pozostała taka sama.
- `unknown`, `unavailable`, usunięte źródło i niepełny odczyt nie kasują
  potwierdzonych wcześniej alarmów. Poprawne `off` kasuje tylko własny sygnał.
- Ogólna flaga awarii pozostaje niezależna od odczytanych szczegółów części 1/4.
- Baza odczekuje 60 sekund braku wszystkich dostępnych stanów binarnych. Przy
  utracie pakietów może wcześniej upłynąć czas ważności danych MQTT. Blueprint
  sprawdza sytuację również co 15 sekund. Po rozruchu obowiązuje dodatkowa ochrona
  przez pierwsze 50 sekund gotowości bazy, bez drugiego pełnego opóźnienia 60 sekund
  w normalnej pracy.
- Powrót łączności oznacza obecność danych, a nie brak alarmów ani kompletność
  wszystkich odczytów. Działający CT 106 nie gwarantuje działającego ETHM/MQTT.
- Wyłączenie wiadomości o powrocie nie blokuje resetowania pamięci zgłoszonej
  utraty łączności. Następna przerwa nadal może zostać zgłoszona.
- Wiadomość wymienia do 12 nowych i 12 ustępujących przyczyn. Pełna pamięć jest
  w atrybucie `active` sensora. Przy wyłączonych wiadomościach o ustąpieniu
  raport zawiera wyłącznie nowe przyczyny.

Gateway nadal pracuje tylko do odczytu. Blueprinty nie dodają nowych komend
SATEL, napięć zasilania w V ani procentowej jakości radia ABAX2. Obejmują dane,
które gateway już publikuje, w tym obsługiwane szczegółowe awarie modułów
oraz manipulatorów.

## Sprawdzenie po instalacji

1. Upewnij się, że pomocniki istnieją, gotowość ma stan `on`, a nowe automatyzacje
   są włączone. Sprawdź dziennik HA pod kątem błędów konfiguracji i szablonów.
2. Na stanowisku testowym wywołaj kontrolowaną zmianę sygnału alarmowego i sprawdź
   wiadomość oraz informację po jego ustąpieniu. Zwykłe naruszenie PIR nie jest
   alarmem strefy.
3. Na stanowisku testowym zatrzymaj samą usługę gatewaya na czas dłuższy niż
   wygaśnięcie MQTT i 60 sekund zwłoki. Sprawdź komunikat braku danych, a po
   uruchomieniu — jeden komunikat o ich powrocie. Nie trzeba zatrzymywać centrali.

Pliki i szablony są sprawdzane lokalnie, ale publikacja na GitHubie nie oznacza
przeprowadzenia testu w Twoim HA. PUSH zależy także od HA, usługi telefonu i sieci;
zapisana pamięć nie stanowi potwierdzenia doręczenia. Krótkie zdarzenia nieodebrane
przez gateway/HA oraz impulsy kończące się w oknie inicjalizacji nie mogą być
odtworzone. Usunięta lub wyłączona encja nie potwierdza ustąpienia jej alarmu.

## Aktualizacja

Blueprinty aktualizuj przez ponowny import/reimport w HA z tych samych adresów.
Zachowuj istniejące automatyzacje i ich ustawienia. Jeśli zmienia się baza pamięci,
instrukcja wydania wskaże konieczność podmiany pliku i restartu HA. Zwykła zmiana
odbiorcy albo opcji powiadomień odbywa się w formularzu automatyzacji.

Pełny stary pakiet `packages/satel_notifications.yaml` pozostaje w repozytorium
jako wariant bez blueprintów. Wybierz jeden wariant instalacji; nie łącz obu.

## Lokalne testy plików

Testy sprawdzają podstawienie pól blueprintu, wykonanie szablonów na zdarzeniach,
wyłączenie recovery, wybranego odbiorcę, brak danych i ochronę rozruchu. Nie
uruchamiają Home Assistant ani nie wysyłają żadnych wiadomości.

Z katalogu repozytorium, w osobnym środowisku Python:

```sh
python -m pip install -r tests/requirements.txt
python tests/check_blueprints.py
```

## Dokumentacja HA

- [Schemat blueprintów](https://www.home-assistant.io/docs/blueprint/schema/)
- [Selektory pól formularza](https://www.home-assistant.io/docs/blueprint/selectors/)
- [Pakiety konfiguracji](https://www.home-assistant.io/docs/configuration/packages/)
- [Sensory szablonowe i odtwarzanie pamięci](https://www.home-assistant.io/integrations/template/)
