# Windows-Firewall — enge Host-Allowlist (optional, Admin)

Ziel: `grok.exe` darf **nur** noch

1. den **lokalen Filter-Proxy** (`127.0.0.1:18743`) und  
2. **`auth.x.ai`** (Login/Token)

erreichen. Alles andere (inkl. `storage.googleapis.com`, `code.grok.com`, …) wird geblockt.

> **Warnung:** Zu eng = Login/Chat bricht. Zuerst Proxy-only testen, dann Firewall.

## Voraussetzung

- Proxy läuft: `scripts\start_proxy.cmd`
- Grok startet mit: `scripts\start_grok_filtered.cmd`  
  (`GROK_CLI_CHAT_PROXY_BASE_URL=http://127.0.0.1:18743/v1`)

## Manuell (Windows-Sicherheit)

1. **Windows-Sicherheit** → Firewall → Erweiterte Einstellungen  
2. **Ausgehende Regeln** → Neue Regel → Programm  
3. Programm: `%USERPROFILE%\.grok\bin\grok.exe` (und ggf. `agent.exe`)  
4. Aktion: **Verbindung blockieren** als Default-Idee — besser:  

### Empfohlene Strategie

**A) Block-Regel (breit)** für `grok.exe` ausgehend = block  
**B) Allow-Regeln davor (höhere Priorität):**

| Regel | Remote |
|-------|--------|
| Allow | `127.0.0.1` / `::1` (lokaler Proxy) |
| Allow | `auth.x.ai` (HTTPS 443) |

Windows-Firewall filtert oft nach Programm + Port, nicht immer elegant nach DNS-Name. Praktisch:

1. Allow TCP out zu **Localport any → Remote 127.0.0.1:18743** für grok.exe  
2. Allow TCP out **443** zu den IP-Adressen von `auth.x.ai` (können sich ändern!)  
3. Block rest für grok.exe  

DNS-IP-Wechsel macht **B** wartungsintensiv. Deshalb ist die Firewall **optional** und der **Proxy der Kern**.

## PowerShell-Skizze (Admin, anpassen!)

```powershell
# Pfade anpassen
$grok = "$env:USERPROFILE\.grok\bin\grok.exe"

# Allow localhost proxy
New-NetFirewallRule -DisplayName "Grok Privacy Allow Local Proxy" `
  -Direction Outbound -Program $grok -Action Allow `
  -RemoteAddress 127.0.0.1 -Protocol TCP -RemotePort 18743

# Allow auth.x.ai — IPs vorher per Resolve-DnsName holen und eintragen
# $ips = (Resolve-DnsName auth.x.ai -Type A).IPAddress
# New-NetFirewallRule ... -RemoteAddress $ips -Protocol TCP -RemotePort 443 -Action Allow

# Block all other outbound for grok (ACHTUNG: nach den Allows)
New-NetFirewallRule -DisplayName "Grok Privacy Block Rest" `
  -Direction Outbound -Program $grok -Action Block
```

Regeln testen: Login + ein Chat. Wenn Login failt → Auth-Allow prüfen.

## macOS / Linux

Analog: `pf`, `iptables`/`nftables` oder Little Snitch / OpenSnitch — nur Loopback:18743 + auth.x.ai:443.

## Deinstallation Firewall

Regeln in der Firewall-UI löschen oder:

```powershell
Get-NetFirewallRule -DisplayName "Grok Privacy*" | Remove-NetFirewallRule
```
