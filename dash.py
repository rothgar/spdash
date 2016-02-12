#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, make_response, g,\
    render_template, redirect, url_for
import os
from os import path
from contextlib import closing
import sqlite3
import socket
import struct
import time, datetime

app = Flask(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'sqdash.db'),
    TFTPDIR='/pxe',
    TFTPFILTER=['default'],
    DEBUG=False
))
app.config.from_envvar('SPDASH_SETTINGS', silent=True)

def connect_db():
    """Connect to the database"""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_db():
    """Connect to db"""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

def set_host_status(h, s):
    """generic method to set host status"""
    db = get_db()
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
    db.execute('insert or replace into all_hosts (hostname, status, timestamp) values (?,?,?)', (h, s, st))
    db.commit()

def is_hex(string):
    """test if string is hex"""
    try:
        int(string, 16)
        return True
    except ValueError:
        return False

def get_hostnames(ips):
    """Get hostnames from list of IPs"""
    hostnames = []
    for ip in ips:
        try:
            # return only shortname of host
            hostnames.append(socket.gethostbyaddr(ip)[0].split('.')[0])
        except:
            hostnames.append(ip)
    return hostnames

def scan_pending_hosts(tftp_dir, ignored_files):
    """Return a list of hostnames from a directory \
        of pxe boot files"""
    ips = []
    pending_hosts = []
    pxe_files = [f for f in os.listdir(tftp_dir) if path.isfile(os.path.join(tftp_dir, f))]
    for rm in ignored_files:
        pxe_files.remove(rm)
    for f in pxe_files:
        # get ip from hex file
        if is_hex(f):
            i = int(f, 16)
            # why is ip hex -> ip address reversed?
            j = '.'.join(reversed(socket.inet_ntoa(struct.pack("<L", i)).split('.')))
            ips.append(j)
        else:
            pending_hosts.append(f)
    for host in get_hostnames(ips):
        set_host_status(host, 'pending')
    return 

@app.teardown_appcontext
def close_db(error):
    """close db connection"""
    if hasattr(g, 'sqlight_db'):
        g.sqlite_db.close()

@app.route('/', methods=["GET"])
def index():
    """render index template"""
    db = get_db()
    cur = db.execute('select hostname, status, build, timestamp from all_hosts where status <> "pending"')
    current_hosts = [dict(hostname=row[0], status=row[1], build=row[2], timestamp=row[3]) for row in cur.fetchall()]
    pend = db.execute('select hostname, status, build, timestamp from all_hosts where status="pending"')
    pending_hosts = [dict(hostname=row[0], status=row[1], build=row[2], timestamp=row[3]) for row in pend.fetchall()]
    return render_template('index.html', current_hosts=current_hosts, pending_hosts=pending_hosts)

@app.route('/pending')
def pending():
    """Pending hosts page"""
    db = get_db()
    pend = db.execute('select hostname, status, build, timestamp from all_hosts where status="pending"')
    pending_hosts = [dict(hostname=row[0], status=row[1], build=row[2], timestamp=row[3]) for row in pend.fetchall()]
    return render_template('pending.html', pending_hosts=pending_hosts)

@app.route('/api/v1/build/<status>/<hostname>')
def update_firstboot_host(status, hostname):
    """set host status"""
    set_host_status(hostname, status)
    return redirect(url_for('index'))

@app.route('/api/v1/delete/<hostname>')
def delete_host(hostname):
    """delete host when build is done"""
    db = get_db()
    db.execute('delete from all_hosts where hostname=?', (hostname,))
    db.commit()
    return redirect(url_for('index'))

@app.route('/api/v1/refresh')
def refresh_pending():
    """refresh pending host list"""
    scan_pending_hosts(app.config['TFTPDIR'], app.config['TFTPFILTER'])
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0')
