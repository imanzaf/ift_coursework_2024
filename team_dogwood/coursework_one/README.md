# IFTE0003 Coursework 1 - Team Dogwood

# Usage Instructions

## Running via Jenkins
### Creating the Docker Containers
1. Update the docker compose file to include the Jenkins service.
```bash
services:
    jenkins:
      image: jenkins/jenkins:lts
      build:
        context: team_dogwood/coursework_one/orchestration/jenkins
        dockerfile: Dockerfile
      restart: unless-stopped
      container_name: jenkins
      ports:
        - "8080:8080"
        - "50000:50000"
      volumes:
        - jenkins_home:/var/jenkins_home
      privileged: true
      user: root  # Need this to handle Docker socket permissions
      environment:
        - JAVA_OPTS=-Djenkins.install.runSetupWizard=false

volumes:
  jenkins_home:
```
2. Run the following command to build containers for postgres, minio, and jenkins.
```bash
docker compose up --build -d jenkins postgres_db_cw postgres_seed_cw miniocw minio_client_cw
```
3. Access the Jenkins UI at `http://localhost:8080`.

### Configuring the Jenkins Pipeline
1. Add your Google API key to the Jenkins credentials manager.
    1. Navigate to: "Manage Jenkins" -> "Credentials" -> "Global" -> "Add Credentials"
    5. Select "Secret text" as the kind.
    6. Enter the name `google_api_key` for the secret ID.
    7. Enter your Google API key as the secret.
    8. Click "OK".
2. Configure the Jenkins pipeline using the UI:
    1. Click on "New Item" in the Jenkins UI.
    2. Enter a name for the pipeline.
    3. Select "Pipeline" as the type.
    4. Click "OK".
    5. In the 'Pipeline Definition' section of the page, select "Pipeline script from SCM".
    6. Select "Git" as the SCM.
    7. Enter the repository URL https://github.com/imanzaf/ift_coursework_2024.
    8. Enter the branch to your current branch. e.g., feature/coursework_one_dogwood
    9. Update the script path to `team_dogwood/coursework_one/orchestration/jenkins/Jenkinsfile`.
    10. Click "Save".

### Runnning the Jenkins Pipeline
1. Click on the pipeline you created in the previous step.
2. Click on "Build Now".

To see the logs of the pipeline:
1. Click on a build number in the "Builds" section of the pipeline page.
2. Click on "Console Output" in the left-hand menu.


## Running locally
*Note: Where the instructions mention the 'root directory of the project', this refers to the `team_dogwood/coursework_one` directory.*

1. Create a .env file in the root directory of the project.
2. Copy the contents of the .env.template file into the .env file. Update the SEARCH_GOOGLE_API_KEY variable with your API key.
3. Run the main script using the following commands:
```bash
# To run the script for retrieving ESG report URLS
poetry run python pipelines/retrieve_store_url/main.py
```
```bash
# To run the script for storing ESG reports in Minio
poetry run python pipelines/retrieve_store_pdf/main.py
```
```bash
# To run the script for updating the postgres database
# Make sure to also pass the required CLI arguments and command as instructed in the file.
# For example:
poetry run python pipelines/manage_companies/main.py remove --symbol AAPL
```

---
# Development Instructions
*Note: Where the instructions mention the 'root directory of the project', this refers to the `team_dogwood/coursework_one` directory.*

### Managing dependencies with Poetry
Poetry is used to manage dependencies for this project. To install the dependencies, run the following command in the root directory of the project:
```bash
poetry install
```

If you use any package as part of your development, you should add it to the `pyproject.toml` file. To do this, run the following command:
```bash
poetry add <package-name>
```

If you decide not to use a package anymore, remove it from the `pyproject.toml` file. To do this, run the following command:
```bash
poetry remove <package-name>
```

### Formatting code with pre-commit hooks
To ensure that the code is formatted correctly and no security vulnerabilities exist, pre-commit hooks are used. Four tools have been added to the hooks: Black, Flake8, Isort, and Bandit. To install the pre-commit hooks, run the following command in the root directory of the project:
```bash
pre-commit install
```

The beauty of pre-commit hooks is that they will automatically be triggered when you make a commit to your branch using the below command:
```bash
git commit -m "Your commit message"
```

If you want to run the pre-commit hooks manually, you can do so by running the following command:
```bash
pre-commit run --all
```

If the pre-commit hooks fail, you will need to fix the issues before you can commit your changes. Black and Isort automatically update your files to fix any issues, flake8 issues need to be dealt with manually.

### Running Unit Tests
To run the unit tests, run the following command in the root directory of the project:
```bash
poetry run pytest
```
