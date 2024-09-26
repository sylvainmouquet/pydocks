# PyDocks

PyDocks is a group of pytest fixures for running tests with Docker containers

### Demonstration:

```python
...
```

## Table of Contents

- [PyDocks](#PyDocks)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Installation](#installation)
  - [Usage](#usage)
  - [License](#license)
  - [Contact](#contact)

## Description

PyDocks is a Python library that provides a set of pytest fixtures for running tests with Docker containers. It simplifies the process of setting up, managing, and tearing down Docker containers during test execution.

Key features include:
- Easy integration with pytest
- Support for PostgreSQL containers
- Automatic container cleanup
- Configurable container settings
- Reusable session-scoped containers for improved test performance

PyDocks is designed to make testing with Docker containers more efficient and less error-prone, allowing developers to focus on writing tests rather than managing infrastructure.

## Installation

```bash
# Install the dependency
pip install pydocks
uv add pydocks
poetry add pydocks
```

## Usage

```python
from pydocks import pydocks

```


## License

PyDocks is released under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For questions, suggestions, or issues related to ReAttempt, please open an issue on the GitHub repository.

