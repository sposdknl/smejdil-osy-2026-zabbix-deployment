#!/usr/bin/python3
"""Initialize a fresh Zabbix DB; never reimport over existing tables."""
import gzip
import os
from pathlib import Path
import subprocess
import pymysql

connection = pymysql.connect(user='root', unix_socket='/var/run/mysqld/mysqld.sock', autocommit=True)
password = os.environ['ZABBIX_DB_PASSWORD']
changed = False
with connection.cursor() as cur:
    cur.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='zabbix'")
    if not cur.fetchone():
        cur.execute('CREATE DATABASE zabbix CHARACTER SET utf8mb4 COLLATE utf8mb4_bin')
        changed = True
    cur.execute("SELECT 1 FROM mysql.user WHERE User='zabbix' AND Host='localhost'")
    if not cur.fetchone():
        cur.execute("CREATE USER 'zabbix'@'localhost' IDENTIFIED BY %s", (password,))
        cur.execute("GRANT ALL PRIVILEGES ON zabbix.* TO 'zabbix'@'localhost'")
        changed = True
    else:
        # Verify supplied credentials rather than rotating an existing password.
        test = pymysql.connect(user='zabbix', password=password, database='zabbix',
                               unix_socket='/var/run/mysqld/mysqld.sock')
        test.close()
    cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='zabbix'")
    table_count = cur.fetchone()[0]
    if table_count == 0:
        candidates = [Path('/usr/share/zabbix/sql-scripts/mysql/server.sql.gz'),
                      Path('/usr/share/zabbix-sql-scripts/mysql/server.sql.gz')]
        schema = next(p for p in candidates if p.exists())
        cur.execute('SELECT @@GLOBAL.log_bin_trust_function_creators')
        previous = int(cur.fetchone()[0])
        try:
            cur.execute('SET GLOBAL log_bin_trust_function_creators=1')
            with gzip.open(schema, 'rb') as sql:
                subprocess.run(['mysql', '--user=root', '--default-character-set=utf8mb4', 'zabbix'],
                               input=sql.read(), check=True)
        finally:
            cur.execute('SET GLOBAL log_bin_trust_function_creators=%s', (previous,))
        changed = True
    # A partial import must fail visibly instead of silently continuing.
    cur.execute('SELECT mandatory, optional FROM zabbix.dbversion')
    version = cur.fetchone()
    if version is None:
        raise RuntimeError('Schema data is missing; restore the snapshot before retrying the import')
    cur.execute('SELECT COUNT(*) FROM zabbix.users')
    if cur.fetchone()[0] == 0:
        raise RuntimeError('Initial Zabbix data is incomplete; refusing to reimport over existing tables')
    print('Database version:', version)
connection.close()
print('DATABASE_CHANGED' if changed else 'DATABASE_OK')
