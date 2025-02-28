from modules.db.db_connection import db

class FileReport(db.Model):
    __tablename__ = 'file_report'

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), nullable=False)
    report_date = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"<FileReport {self.company_name} {self.report_date} {self.file_name}>"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
