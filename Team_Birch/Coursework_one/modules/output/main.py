from flask import Flask, request, jsonify, render_template,session,flash,redirect,url_for
from modules.db.db_connection import init_db, db
from modules.input.input_loader import upload_files_to_minio
from models import FileReport
from models import User
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(24)

# initialize
init_db(app)


@app.route('/', methods=['GET','POST'])
def login():
    error_message = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            #flash('登录成功！', 'success')
            return redirect(url_for('upload_file'))
        else:
            error_message = '用户名或密码错误'
    return render_template('login.html', error_message=error_message)


@app.route('/upload', methods=['POST','GET'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'files' not in request.files:
            return jsonify({"error": "No file part"}), 400
        files = request.files.getlist('files')
        company_name = request.form['company_name']
        report_date = request.form['report_date']

        # check if company
        if not files:
            return jsonify({"error": "No files uploaded."}), 400

        try:
            # save MinIO
            file_urls = upload_files_to_minio(files, company_name, report_date)

            # mete data to database
            for url in file_urls:
                new_report = FileReport(
                    company_name=company_name,
                    report_date=report_date,
                    file_name=f"{company_name}_{report_date}_CSR.pdf",
                    file_url=url
                )
                db.session.add(new_report)

            # commit
            db.session.commit()
            return redirect(url_for('home'))
        except Exception as e:
            db.session.rollback()  # 回滚数据库事务
            return jsonify({"error": str(e)}), 500

    return render_template('upload.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
    # 确保用户已登录
    if 'user_id' not in session:
        return redirect(url_for('login'))


    company_name = request.form.get('company_name')
    report_date = request.form.get('report_date')

    # get report
    query = FileReport.query

    # filter
    if company_name:
        query = query.filter(FileReport.company_name.like(f'%{company_name}%'))
    if report_date:
        query = query.filter(FileReport.report_date == report_date)

    reports = query.all()

    return render_template('index.html', reports=reports)


if __name__ == "__main__":
    app.run(debug=True)
