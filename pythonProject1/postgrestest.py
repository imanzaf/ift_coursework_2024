from reports.database import PostgresManager

pg = PostgresManager(host="localhost", port="5439")  
print(pg.check_pdf_record("test.pdf"))  
pg.insert_pdf_record({
    "company": "TestCorp",
    "url": "http://example.com",
    "year": 2024,
    "file_hash": "abc123",
    "filename": "test.pdf"
})
print("Insert successful!")

test_record = {
    "company": "TestCorp",
    "url": "http://example.com",
    "year": 2024,
    "file_hash": "abc123",  # 这里是相同的 file_hash
    "filename": "test.pdf"
}

pg = PostgresManager(host="localhost", port="5439")
pg.insert_pdf_record(test_record)  # 第一次插入，应该成功
pg.insert_pdf_record(test_record)  # 第二次插入，相同 file_hash，应该被拦截
