# Zabbix 8.0 LTS RC2 na ansible-lab

Ansible deployment pro Debian 13 amd64: Zabbix server, frontend a agent 2
`2:8.0.0~rc2-1+debian13`, Apache s PHP 8.4 a Oracle MySQL 8.4 LTS.
VM má 2 vCPU, 2 GB RAM a 20 GB disk. Jde o laboratorní konfiguraci.

## Spuštění

Vyžaduje Ansible Core 2.17+ a `sshpass` na řídicím počítači.
Na cíli používá účet `malyl` a přepnutí na roota přes `su`.
SSH a root heslo se zadávají interaktivně, nejsou v inventáři.

```bash
cd deployment
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml -k -K
```

V tomto pracovním prostředí je Ansible připravený v
`/tmp/bhyve-ansible-venv/bin/ansible-playbook`.
Inventář obsahuje adresu `192.168.5.205`; před dalším během ověř DHCP adresu.
Soubor `ansible.cfg` používá ověřené SSH klíče hostitelů v
`/tmp/bhyve_automat_known_hosts`. Na jiném počítači cestu uprav
nebo použij svůj standardní `known_hosts`.

Databázové heslo se při prvním běhu vygeneruje do `secrets/db-password`.
Adresář musí mít oprávnění 0700, soubor 0600; nepatří do verzování.
Pro opakované běhy tento soubor zachovej. Přístup k MySQL rootovi je lokální
přes unixový socket. MySQL naslouchá jen na loopbacku.

Playbook zachovává původní konfiguraci agenta (`Server` a `ServerActive`
`192.168.5.1`, metadata `Linux`) i automatické odvození hostname.
Verze Zabbixu je připnutá v APT preferences, aby další běh neinstaloval
novější RC nebo finální vydání. Instalace schématu se provede jen do prázdné
databáze; při částečném importu playbook selže, nepřepisuje data.
Původní shell konfigurace uživatele je zálohovaná jako
`/home/malyl/.bashrc.before-ansible`; neinteraktivní shell přeskočí uvítací výpis.

## Přístup

Web: http://192.168.5.205/zabbix/

Čerstvé schéma používá standardní účet Zabbix `Admin` s heslem `zabbix`.
Frontend je nakonfigurovaný přímo, není potřeba procházet instalačním průvodcem.
Playbook ověřuje Apache, odpověď API `8.0.0`, přesné RC2 verze všech pěti
balíčků a otevřený port serveru 10051. API u RC2 vrací základní verzi bez suffixu.

Ověřeno 22. 10. 2026 na cílové VM: server i agent `8.0.0rc2`, MySQL `8.4.13`,
všechny čtyři služby aktivní, přihlášení a odhlášení přes API úspěšné,
výchozí host `Zabbix server` má lokální agent interface dostupný (`available=1`).
Opakovaný běh: `ok=25 changed=0 unreachable=0 failed=0 skipped=1`.

## Snapshot a návrat

Před instalací byla VM korektně vypnuta a na `hp-proliant` vznikl snapshot:

```text
zroot/vms/ansible-lab@before-zabbix-8-rc2
```

Po úspěšné instalaci a ověření byla VM korektně vypnuta a vznikl také snapshot
`zroot/vms/ansible-lab@after-zabbix-8-rc2`. VM zůstala vypnutá.
Pro návrat k hotové instalaci použij tento název namísto `before-zabbix-8-rc2`
v příkazu rollback níže.

Příkazy na bhyve hostiteli jako root:

```sh
vm stop ansible-lab
# Počkej, až vm list ukáže Stopped.
vm rollback ansible-lab@before-zabbix-8-rc2
vm start ansible-lab
```

Rollback zahodí změny disku od snapshotu, včetně databáze a její konfigurace.
Snapshot neobsahuje RAM. Lokální playbook a secrets na řídicím počítači
rollback neovlivní; následným spuštěním playbooku lze instalaci zopakovat.

## Zdroje

- https://repo.zabbix.com/zabbix/8.0/unstable/debian/
- https://www.zabbix.com/documentation/8.0/en/manual/installation/requirements
- https://www.zabbix.com/documentation/8.0/en/manual/installation/install/packages
- https://dev.mysql.com/doc/mysql-apt-repo-quick-guide/en/
