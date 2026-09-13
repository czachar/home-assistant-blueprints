# Home Assistant — blueprinty

| Blueprint | Zakres | Import |
|---|---|---|
| Serwerownia Monitor 1.3.7 | UPS, VM/LXC, storage, RAM i diagnostyka serwera | [Importuj do HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fczachar%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fserwerownia%2Fserwerownia_monitor_v1.yaml) |
| SATEL — alarmy i awarie 1.1 | Alarmy, sabotaże, dym/zalanie i szczegółowe awarie | [Importuj do HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fczachar%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fsatel%2Fsatel_alarm_notifications.yaml) |
| SATEL — utrata i powrót danych 1.1 | Dostępność danych ETHM/MQTT w HA | [Importuj do HA](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fczachar%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fsatel%2Fsatel_connectivity_notifications.yaml) |

**SATEL wymaga jednorazowej instalacji bazy pamięci.** Przy przejściu ze starego
pakietu zastąp go bazą, aby uniknąć podwójnych powiadomień.

[Instrukcja instalacji i migracji SATEL](docs/satel-notifications/README_PL.md)

[Przykład konfiguracji Serwerowni z CT 106](examples/serwerownia_monitor_ct106.yaml)
