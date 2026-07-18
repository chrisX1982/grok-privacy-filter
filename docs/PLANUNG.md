# ROADMAP – Grok Privacy Filter

**Ziel:** Das Tool für die Mehrheit der Nutzer deutlich einfacher nutzbar machen, ohne die bestehenden Stärken (Transparenz + volle Anpassbarkeit) aufzugeben.

---

## Vision (Goldene Mitte)

- Der **technische Kern** (Proxy, Policy, Hooks, Opt-out, Config) bleibt **voll offen, transparent und maximal anpassbar**.
- Die **GUI** wird zum **empfohlenen Standard-Einstieg** für die meisten Nutzer.
- Es gibt einen klaren, einfachen Nutzungspfad („Ich will einfach mehr Privacy“) und einen fortgeschrittenen Pfad für Power-User / Anpasser.
- Transparenz und Ehrlichkeit (wie in `GRENZEN.md`) bleiben erhalten.

---

## Grundsätze (nicht verhandelbar)

- Keine Blackbox. Alles muss nachvollziehbar und editierbar bleiben.
- Keine falschen Versprechungen.
- Die bestehende Offenheit und Anpassbarkeit wird **nicht** eingeschränkt.
- Neue Komfortschichten (GUI, Installer etc.) sind optional – der manuelle Weg bleibt immer möglich.

---

## Phasenplan

### Phase 1: GUI stabilisieren & für echte Nutzung bereit machen (Höchste Priorität)

**Ziel:** Die GUI funktioniert bei anderen Leuten ohne manuelle Anpassungen und wird der natürliche Einstiegspunkt.

**Aufgaben:**

1. **Pfade dynamisch machen** (statt hardcoded `C:\Users\chris\...`)
   - Proxy-Pfad, Log-Pfad, Policy-Pfad, Python-Erkennung etc. automatisch ermitteln.
   - Fallbacks für Windows + Unix-Systeme einbauen.

2. **GUI beim ersten Start prüfen**, ob alles korrekt installiert ist (Proxy vorhanden? Policy vorhanden? Python verfügbar?).

3. **Bessere Fehlermeldungen** in der GUI einbauen.

4. **Datenklau-Schutz-Status** noch klarer und prominenter darstellen.

5. **GUI als eigenständigen Starter** verfügbar machen (z. B. `start_gui.py` oder Eintrag in den Install-Skripten).

**Ergebnis Phase 1:** Jemand kann die GUI starten und sie funktioniert ohne Code-Änderungen.

---

### Phase 2: Einfachen Nutzungspfad schaffen

**Ziel:** Die meisten Nutzer brauchen nach der Installation nur noch die GUI.

**Aufgaben:**

6. **Verbesserten Quick-Install** erstellen (z. B. `install --easy` oder separates `install_easy.ps1` / `install_easy.sh`).
   - Macht die wichtigsten Defaults automatisch (Opt-out, Proxy, Hook, Config-Snippet).
   - Startet danach direkt die GUI.

7. **GUI als Standard-Einstieg positionieren**.
   - In README und `ANLEITUNG.md` klar kommunizieren: „Für die meisten Nutzer reicht die GUI“.

8. **Optionale „One-Click-Defaults“** in der GUI.
   - Button „Empfohlene Datenschutz-Einstellungen übernehmen“ (aktiviert alle kritischen deny-Pfade + gute Defaults).

**Ergebnis Phase 2:** Ein normaler Entwickler kann das Tool in wenigen Schritten nutzen, ohne tief in Config oder Policy einzutauchen.

---

### Phase 3: Dokumentation & Onboarding verbessern

**Ziel:** Klare Trennung zwischen „einfach nutzen“ und „anpassen“.

**Aufgaben:**

9. **Zweigleisige Dokumentation** schaffen:
   - Kurzer Abschnitt „Schnellstart für die meisten Nutzer“ (5–10 Min.)
   - Bestehende detaillierte Anleitung bleibt für Fortgeschrittene erhalten.

10. **README.md** anpassen:
    - Oben klar machen, welcher Weg für wen gedacht ist.
    - GUI prominenter bewerben.

11. **Erststart-Erlebnis** in der GUI verbessern (kurzer Willkommenshinweis + Status-Check).

**Ergebnis Phase 3:** Neue Nutzer verstehen sofort, wie sie starten sollen, ohne überfordert zu sein.

---

### Phase 4 (optional / später)

- Bessere visuelle Aufbereitung der GUI
- Autostart-Option direkt aus der GUI
- Einfache Möglichkeit, Proxy + GUI zusammen zu starten
- Langfristig: Überlegung eines kleinen Installer-Pakets (mit Bedacht wegen Transparenz)

---

## Vorgeschlagene Reihenfolge

| Phase | Fokus                        | Reihenfolge der Tasks     | Geschätzter Aufwand |
|-------|------------------------------|---------------------------|---------------------|
| 1     | GUI stabilisieren            | 1 → 2 → 3 → 4 → 5         | Mittel              |
| 2     | Einfacher Nutzungspfad       | 6 → 7 → 8                 | Mittel              |
| 3     | Dokumentation & Onboarding   | 9 → 10 → 11               | Niedrig             |
| 4     | Nice-to-have                 | nach Bedarf               | —                   |

---

**Status:** Entwurf – Juli 2026

> Dieser Plan ist als lebendes Dokument gedacht. Er kann bei Bedarf angepasst und erweitert werden.