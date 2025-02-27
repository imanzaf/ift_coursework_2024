import psycopg2
import yaml
import os


def load_config():
    base_dir = os.path.dirname(os.path.realpath(__file__))
    conf_path = os.path.join(base_dir, "..", "..", "config", "conf.yaml")
    with open(conf_path, "r") as f:
        return yaml.safe_load(f)


def get_db_connection():
    """返回一个PostgreSQL连接对象"""
    config = load_config()
    db_conf = config["database"]["postgresql"]
    conn = psycopg2.connect(
        host=db_conf["host"],
        port=db_conf["port"],
        user=db_conf["user"],
        password=db_conf["password"],
        dbname=db_conf["dbname"],
    )
    return conn


def init_db():
    """
    初始化数据库，创建 `csr_reporting.company_static`（如题目要求）。
    注意：必须先在PostgreSQL里手动CREATE SCHEMA csr_reporting。
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE SCHEMA IF NOT EXISTS csr_reporting;
        CREATE TABLE IF NOT EXISTS csr_reporting.company_static (
            id SERIAL PRIMARY KEY,
            company_name TEXT NOT NULL,
            website TEXT,
            csr_report_url TEXT,
            csr_report_year INT,
            storage_path TEXT
        );
    """
    )
    conn.commit()
    cur.close()
    conn.close()
