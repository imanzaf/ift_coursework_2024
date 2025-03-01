# Team Sakura - Project Instructions

How to run the code

1. Clone the github 
2. copy file docker-compose.yaml from team_sakura/coursework_one/a_pipeline/config to the root of the project
2. Set up your GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID keys by duplicating the .env.template from team_sakura/coursework_one/a_pipeline/config, naming it .env and adding it to the root of the project.
3. Add your absolute local path to Equity.db in conf.yaml
4. Open Docker Desktop 
5. In your project go to terminal and run
```
docker compose up --build miniocw mongo_db jenkins  pipeline_runner minio_client_cw
```
6. In terminal run **export PATH="$HOME/.local/bin:$PATH"**
7. Run **"poetry install"**
8. Run main.py with poetry with **"poetry run python a_pipeline/main.py"** to extract CSR reports and store them on mongo_db and minio.


To run scheduling with Jenkins : 
1. Navigate to Jenkins Web UI via: http://localhost:8080.
2. Obtain password using:
**"docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword"** on docker desktop terminal | username is **"admin"**
3. Install necessary plugins and don't forget the **Pipeline plugin**
4. Create a new task: Select Pipeline under "New Item" and name the task **run main.py**
5. In Configuration, select **Build periodically in Triggers section**
6. Enter the following cron expression in the Schedule field: **0 1 * * 1**
7. Under the Pipeline section, choose Pipeline script and input the script:

```
pipeline {
    agent any
    stages {
        stage('Run main.py') {
            steps {
                script {
                    retry(3) { // Retry three times after failure
                        sh 'docker exec pipeline_runner poetry run python /app/a_pipeline/main.py'
                    }
                }
            }
        }
    }
}
```
8. save your changes and click on **build now** if you want to run the scheduler now, otherwise, it runs every Monday at 1:00 AM. 

Running the code locally
1. Add your absolute local path to Equity.db
2. Run **"docker compose up --build miniocw mongo_db jenkins  pipeline_runner minio_client_cw"**
1. Navigate to coursework_one directory in terminal 
2. In terminal run **export PATH="$HOME/.local/bin:$PATH"**
3. Run **"poetry install"**
4. Run **"poetry run python a_pipeline/main.py"** to extract CSR reports and store them on mongo_db and minio.
5. Run **"poetry run python a_pipeline/modules/url_parser/app.py"** to access web interface by accessing http://127.0.0.1:5000
6. Run **"poetry run python a_pipeline/modules/url_parser/api.py"** to use api by running commands such as **"Curl -X 'GET' http://0.0.0.0:8000/reports?report_year=2023  "**


Poetry Commands

| command                                                               |  Description              |
|-----------------------------------------------------------------------|---------------------------------------------|
| poetry init                                                           |  Initialize Poetry in an existing project   |
| poetry add requests pymongo python-dotenv minio pyyaml beautifulsoup4 |  This installs the dependencies and updates pyproject.toml and poetry.lock.|
| poetry add --group dev pytest black flake8                            | Development dependencies (e.g., testing and formatting tools) should be installed separately|
| poetry remove requests                                                | To remove a package|
| poetry run python a_pipeline/ main.py                                 | to extract CSR reports and store them on mongo_db and minio|
