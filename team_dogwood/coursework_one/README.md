# IFTE0003 Coursework 1 - Team Dogwood

## Usage Instructions

## Development Instructions
*Note: Where the instructions mention the 'root directory of the project', this refers to the `team_dogwood/coursework_one` directory.*

#### Managing dependencies with Poetry
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

#### Formatting code with pre-commit hooks
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

#### Running Unit Tests
To run the unit tests, run the following command in the root directory of the project:
```bash
poetry run pytest
```
