# Cerebral Centaurs

## Project Setup

1. Install python 3.10.X: [Download](https://www.python.org/downloads/)
2. Install poetry (note that poetry is installed globally) [Installation](https://python-poetry.org/docs/#installation)
3. Navigate to your project folder and initialize virtual environment
```bash
poetry env use path/to/your/python3.10/executable
```
4. Install dependencies
```bash
poetry install
```
5. Install `pre-commit` hooks (will be cached)
```bash
poetry run pre-commit install
```
6. Create a new feature branch
```bash
git checkout -b my_feature_name
```
7. Add your code, push and create a PR (github) - that will trigger tests and pre-commit hooks. **Note that working directly on main branch is prohibited!**
8. If you edit pyproject.toml remember to run poetry lock command!
```bash
poetry lock
```
10. Manually running pre-commit hooks:
```
poetry run pre-commit run --all-files
```

9. For local unit testing, please use `pytest`:
```
poetry run pytest tests --cov=codejam --cov=tests --cov-report=term-missing
```

## Project launch
Run the server
```bash
poetry run uvicorn codejam.server.application:app --reload
```

Start the clients in separate windows
```bash
poetry run python codejam/client/client.py
```

## Tools brief summary

### flake8: general style rules

Our first and probably most important tool is flake8. It will run a set of plugins on your codebase and warn you about any non-conforming lines.
Here is a sample output:
```
~> flake8
./app.py:1:6: N802 function name 'helloWorld' should be lowercase
./app.py:1:16: E201 whitespace after '('
./app.py:2:1: D400 First line should end with a period
./app.py:2:1: D403 First word of the first line should be properly capitalized
./app.py:3:19: E225 missing whitespace around operator
```

Each line corresponds to an error. The first part is the file path, then the line number, and the column index.
Then comes the error code, a unique identifier of the error, and then a human-readable message.

If, for any reason, you do not wish to comply with this specific error on a specific line, you can add `# noqa: CODE` at the end of the line.
For example:
```python
def helloWorld():  # noqa: N802
    ...
```
will pass linting. Although we do not recommend ignoring errors unless you have a good reason to do so.

It is run by calling `flake8` in the project root.

#### Plugin List:

- `flake8-docstring`: Checks that you properly documented your code.

### ISort: automatic import sorting

This second tool will sort your imports according to the [PEP8](https://www.python.org/dev/peps/pep-0008/#imports). That's it! One less thing for you to do!

It is run by calling `isort .` in the project root. Notice the dot at the end, it tells ISort to use the current directory.

### Pre-commit: run linting before committing

This third tool doesn't check your code, but rather makes sure that you actually *do* check it.

It makes use of a feature called [Git hooks](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks) which allow you to run a piece of code before running `git commit`.
The good thing about it is that it will cancel your commit if the lint doesn't pass. You won't have to wait for Github Actions to report and have a second fix commit.

It is *installed* by running `pre-commit install` and can be run manually by calling only `pre-commit`.

[Lint before you push!](https://soundcloud.com/lemonsaurusrex/lint-before-you-push)

#### Hooks List:

- `check-toml`: Lints and corrects your TOML files.
- `check-yaml`: Lints and corrects your YAML files.
- `end-of-file-fixer`: Makes sure you always have an empty line at the end of your file.
- `trailing-whitespaces`: Removes whitespaces at the end of each line.
- `python-check-blanket-noqa`: Forbids you from using noqas on large pieces of code.
- `isort`: Runs ISort.
- `flake8`: Runs flake8.
- `mypy`: Runs mypy type checking
- `black`: Runs black code formatter
