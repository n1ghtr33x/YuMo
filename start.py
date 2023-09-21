from subprocess import Popen, PIPE

api_id = input('API_ID: ')
api_hash = input('API_HASH: ')
database_type = input('Choose database type:\n[1] MongoDB db_url\n[2] Sqlite (default)\n')

if database_type == 1:
    db_name = "YuMo_Userbot"
    db_type = "mongodb"
    db_url = input('Database url: ')
else:
    db_name = "db.sqlite3"
    db_type = "sqlite3"
    db_url = 'None'

f = open('.env', 'w')
f.write(f'API_ID={api_id}\n')
f.write(f'API_HASH={api_hash}\n')
f.write(f'DATABASE_TYPE={db_type}\n')
f.write(f'DATABASE_NAME={db_name}\n')
f.write(f'DATABASE_URL={db_url}\n')

cmd_obj = Popen(
        "python3 install.py 3",
        shell=True,
        stdout=PIPE,
        stderr=PIPE,
        text=True,
    )

print("""============================
Great! YuMo Userbot installed successfully!
Start with: \\"python3 main.py\\
============================""")
