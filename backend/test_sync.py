import psycopg2

try:
    conn = psycopg2.connect(
        dbname="cube27",
        user="postgres",
        password="postgres",
        host="127.0.0.1",
        port=5432
    )
    print("✅ УСПЕХ! Синхронное подключение работает!")
    conn.close()
except Exception as e:
    print("❌ Ошибка синхронного подключения:")
    print(e)