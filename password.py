import sqlite3
import os
import secrets
import string
import pyperclip
from cryptography.exceptions import InvalidTag
from crypto_engine import derive_key_super_secure, encrypt_password, decrypt_password
from database import DB_NAME, init_db 

def generate_powerful_password(length=25):
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def get_vault_salt():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT salt FROM master_data WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def setup_vault():
    print("--- FIRST TIME SETUP ---")
    while True:
        p1 = input("Set Master Password: ")
        p2 = input("Confirm Master Password: ")
        if p1 == p2:
            break
        print("Passwords do not match")
    
    salt = os.urandom(32)
    key, _ = derive_key_super_secure(p1, salt)
    canary = encrypt_password(key, "VAULT_OPEN")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO master_data (id, salt) VALUES (1, ?)", (salt,))
    cursor.execute("INSERT INTO passwords (site_name, username, encrypted_bundle) VALUES (?, ?, ?)", ("_canary", "system", canary))
    conn.commit()
    conn.close()
    return p1

def verify_vault(master_password):
    salt = get_vault_salt()
    if not salt: return False
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT encrypted_bundle FROM passwords WHERE site_name = '_canary'")
    bundle = cursor.fetchone()[0]
    conn.close()
    key, _ = derive_key_super_secure(master_password, salt)
    try:
        decrypt_password(key, bundle)
        return True
    except InvalidTag:
        return False

def add_entry(master_password, site_name, username, site_password):
    salt = get_vault_salt()
    key, _ = derive_key_super_secure(master_password, salt)
    bundle = encrypt_password(key, site_password)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO passwords (site_name, username, encrypted_bundle) VALUES (?, ?, ?)', (site_name, username, bundle))
    conn.commit()
    conn.close()
    print(f"SUCCESS: {site_name} saved")

def get_entry(master_password, site_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT username, encrypted_bundle FROM passwords WHERE site_name = ?', (site_name,))
    result = cursor.fetchone()
    conn.close()
    if not result or site_name == "_canary":
        print("Not Found")
        return
    user, bundle = result
    salt = get_vault_salt()
    key, _ = derive_key_super_secure(master_password, salt)
    try:
        plain = decrypt_password(key, bundle)
        pyperclip.copy(plain)
        print(f"Username: {user}\nPassword: {plain}\nCopied to clipboard")
    except InvalidTag:
        print("Decryption Failed")

def list_entries():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT site_name FROM passwords WHERE site_name != '_canary' ORDER BY site_name ASC")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        print(f"- {row[0]}")

def search_entries(query):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT site_name FROM passwords WHERE site_name LIKE ? AND site_name != '_canary'", ('%' + query + '%',))
    rows = cursor.fetchall()
    conn.close()
    if not rows:
        print("No matches found")
    else:
        for row in rows:
            print(f"- {row[0]}")

def delete_entry(site_name):
    if site_name == "_canary": return
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM passwords WHERE site_name = ?', (site_name,))
    conn.commit()
    cursor.execute('VACUUM')
    conn.close()
    print(f"Deleted {site_name}")

def change_master_password(old_password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT site_name, username, encrypted_bundle FROM passwords')
    rows = cursor.fetchall()
    old_salt = get_vault_salt()
    old_key, _ = derive_key_super_secure(old_password, old_salt)
    decrypted_entries = []
    try:
        for site, user, bundle in rows:
            if site == "_canary":
                decrypted_entries.append((site, user, "VAULT_OPEN"))
            else:
                decrypted_entries.append((site, user, decrypt_password(old_key, bundle)))
    except InvalidTag:
        print("Error")
        return old_password
    new_p1 = input("New Master Password: ")
    new_p2 = input("Confirm: ")
    if new_p1 != new_p2:
        return old_password
    new_salt = os.urandom(32)
    new_key, _ = derive_key_super_secure(new_p1, new_salt)
    cursor.execute('DELETE FROM passwords')
    for site, user, plain in decrypted_entries:
        new_bundle = encrypt_password(new_key, plain)
        cursor.execute('INSERT INTO passwords (site_name, username, encrypted_bundle) VALUES (?, ?, ?)', (site, user, new_bundle))
    cursor.execute('UPDATE master_data SET salt = ? WHERE id = 1', (new_salt,))
    conn.commit()
    cursor.execute('VACUUM')
    conn.close()
    print("Changed")
    return new_p1

def main_menu():
    init_db()
    print("""
    ***************************
    * SECURE VAULT v1.0     *
    ***************************
    """)
    if not get_vault_salt():
        current_master = setup_vault()
    else:
        while True:
            current_master = input("Master Password: ")
            if verify_vault(current_master):
                break
            print("Access Denied")

    while True:
        print("\n1:Add 2:Get 3:List 4:Search 5:Delete 6:ChangeMaster 7:Exit")
        c = input("> ")
        if c == '1':
            site, user = input("Site: "), input("User: ")
            pwd = generate_powerful_password() if input("Gen? (y/n): ").lower() == 'y' else input("Pass: ")
            if len(pwd) > 20: print(f"Generated: {pwd}")
            add_entry(current_master, site, user, pwd)
        elif c == '2':
            get_entry(current_master, input("Site: "))
        elif c == '3':
            list_entries()
        elif c == '4':
            search_entries(input("Query: "))
        elif c == '5':
            delete_entry(input("Delete site: "))
        elif c == '6':
            current_master = change_master_password(current_master)
        elif c == '7':
            break

if __name__ == "__main__":
    main_menu()