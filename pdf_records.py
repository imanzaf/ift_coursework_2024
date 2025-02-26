import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5439,
    dbname="postgres",
    user="postgres",
    password="postgres"
)

cur = conn.cursor()
cur.execute("SELECT company, url, filename FROM pdf_records;")
rows = cur.fetchall()

print("Stored PDFs:")
for row in rows:
    print(f"Company: {row[0]}, URL: {row[1]}, Filename: {row[2]}")

cur.close()
conn.close()
