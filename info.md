# Network Map

Visualizza e monitora i dispositivi della tua rete locale su una mappa interattiva direttamente in Home Assistant.

## Caratteristiche

- **Monitoraggio via ping** ogni 60 secondi
- **Supporto IP dinamici** tramite risoluzione MAC address (ARP)
- **Config Flow** nativo per aggiungere dispositivi dall'UI
- **Entità `binary_sensor`** per ogni dispositivo con stato online/offline
- **Card Lovelace** con nodi trascinabili e persistenza posizioni
- Tipi supportati: videocamera, NAS, switch, access point, router, server, generico

## Installazione Card

Questo repository contiene solo l'integrazione backend. Per la card Lovelace grafica, installa anche il plugin **Network Map Card** da HACS o manualmente.
