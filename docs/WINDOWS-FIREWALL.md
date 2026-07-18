# Windows Firewall — strict host allow-list (optional, requires admin)

Goal: `grok.exe` may **only** reach

1. the **local filter proxy** (`127.0.0.1:18743`) and  
2. **`auth.x.ai`** (login / token)

Everything else (including `storage.googleapis.com`, `code.grok.com`, …) is blocked.

> **Warning:** Too strict = login/chat breaks. Test with proxy-only first, then add the firewall.

## Prerequisite

- Proxy is running: `scripts\start_proxy.cmd`
- Grok starts with: `scripts\start_grok_filtered.cmd`  
  (`GROK_CLI_CHAT_PROXY_BASE_URL=http://127.0.0.1:18743/v1`)

## Manual (Windows Security)

1. **Windows Security** → Firewall → Advanced settings  
2. **Outbound rules** → New rule → Program  
3. Program: `%USERPROFILE%\.grok\bin\grok.exe` (and possibly `agent.exe`)  
4. Action: **Block connection** as the default idea — better:

### Recommended strategy

**A)** Create a broad **Block rule** for outbound `grok.exe`  
**B)** Create **Allow rules before it** (higher priority):

| Rule | Remote |
|------|--------|
| Allow | `127.0.0.1` / `::1` (local proxy) |
| Allow | `auth.x.ai` (HTTPS 443) |

Windows Firewall often filters by program + port, not always cleanly by DNS name. In practice:

1. Allow TCP outbound to **local port any → remote 127.0.0.1:18743** for grok.exe  
2. Allow TCP outbound **443** to the IP addresses of `auth.x.ai` (these can change!)  
3. Block everything else for grok.exe  

Because DNS IPs change, **B** requires maintenance. That is why the firewall is **optional** and the **proxy is the core**.

## PowerShell sketch (run as Admin, adapt!)

```powershell
# Adapt paths
$grok = "$env:USERPROFILE\.grok\bin\grok.exe"

# Allow localhost proxy
New-NetFirewallRule -DisplayName "Grok Privacy Allow Local Proxy" `
  -Direction Outbound -Program $grok -Action Allow `
  -RemoteAddress 127.0.0.1 -Protocol TCP -RemotePort 18743

# Allow auth.x.ai — resolve IPs first and insert them
# $ips = (Resolve-DnsName auth.x.ai -Type A).IPAddress
# New-NetFirewallRule ... -RemoteAddress $ips -Protocol TCP -RemotePort 443 -Action Allow

# Block all other outbound for grok (CAUTION: after the Allow rules)
New-NetFirewallRule -DisplayName "Grok Privacy Block Rest" `
  -Direction Outbound -Program $grok -Action Block
```

Test the rules: login + one chat. If login fails → check the auth allow rule.

## macOS / Linux

Analogous: `pf`, `iptables`/`nftables` or Little Snitch / OpenSnitch — allow only loopback:18743 + auth.x.ai:443.

## Removing the firewall rules

Delete the rules in the Firewall UI or:

```powershell
Get-NetFirewallRule -DisplayName "Grok Privacy*" | Remove-NetFirewallRule
```
