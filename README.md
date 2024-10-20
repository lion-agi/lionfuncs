```
  _      _____  ____  _   _ ______ _    _ _   _  _____ _____
 | |    |_   _|/ __ \| \ | |  ____| |  | | \ | |/ ____/ ____|
 | |      | | | |  | |  \| | |__  | |  | |  \| | |   | (___
 | |      | | | |  | | . ` |  __| | |  | | . ` | |    \___ \
 | |____ _| |_| |__| | |\  | |    | |__| | |\  | |________) |
 |______|_____\____/|_| \_|_|     \____/|_| \_|\_____|_____/

```

# lionfuncs: Empowering Python Development 🦁

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/lionfuncs.svg)](https://badge.fury.io/py/lionfuncs)
![PyPI - Downloads](https://img.shields.io/pypi/dm/lionfuncs?color=blue)
![Discord](https://img.shields.io/discord/1167495547670777866?color=7289da&label=discord&logo=discord)

---

## 🌟 Key Features

- 🔢 **Efficient Data Handling**: Robust functions for complex data structures
- 🔍 **Advanced Parsing**: Tools for JSON, Markdown, and text parsing
- 🧮 **Algorithmic Operations**: Similarity and distance algorithms
- 🐼 **Enhanced Pandas Integration**: Extended DataFrame functionality
- 🔄 **Flexible Type Conversions**: Seamless data type conversions
- 📦 **Package Management**: Import and package operation utilities

---

## 🏗️ Library Structure and Capabilities

```
lionfuncs
├── algo        # Algorithmic operations
├── data        # Data handling and manipulation
├── parse       # Parsing utilities
├── func        # Function handling and decorators
├── package     # Package and import management
└── integrations# Integrations (e.g., pandas)
```

- **algo**: Implements various similarity and distance algorithms (e.g., cosine, Levenshtein, Jaro-Winkler).
- **data**: Provides tools for efficient manipulation of complex data structures, including nested dictionaries and lists.
- **parse**: Offers advanced parsing capabilities for JSON, Markdown, and other text formats, with robust error handling.
- **func**: Includes decorators and utilities for function manipulation, async operations, and error handling.
- **package**: Manages package imports and provides tools for dynamic module loading and version checking.
- **integrations**: Extends functionality of popular libraries like pandas, offering optimized operations on DataFrames.

---

## 🚀 Quick Start

### Installation

Choose the method that best suits your needs:

```bash
# For stable release
pip install lionfuncs

# For latest development version
pip install git+https://github.com/lion-agi/lionfuncs.git

# If you're using poetry
poetry add lionfuncs
```

Compatibility: lionfuncs supports Python 3.7+

### Basic Usage

```python
from lionfuncs.data import to_dict
from lionfuncs.parse import md_to_json
from lionfuncs.algo import cosine_similarity

# Convert string to dict
data = to_dict('{"name": "John", "age": 30}')
print(data)  # Output: {'name': 'John', 'age': 30}

# Parse Markdown to JSON
md_text = "# Title\n- Item 1\n- Item 2"
json_data = md_to_json(md_text)
print(json_data)  # Output: {'title': 'Title', 'items': ['Item 1', 'Item 2']}

# Calculate similarity
similarity = cosine_similarity("hello world", "hello there")
print(similarity)  # Output: 0.7071067811865475
```

---

## 📊 Performance and Optimization

lionfuncs is designed with performance in mind:

- Efficient algorithms optimized for Python
- Minimal dependencies to reduce overhead
- Utilizes Python's built-in functions and libraries where possible

In benchmark tests, lionfuncs has shown significant performance improvements in data parsing and manipulation tasks compared to conventional methods.

---

## 🌍 Use Cases

lionfuncs has been successfully used in various domains:

1. **Data Science**: Preprocessing and cleaning large datasets
2. **Web Development**: Parsing and manipulating JSON data from APIs
3. **Text Analysis**: Implementing advanced search and similarity algorithms
4. **DevOps**: Automating package management and deployment processes

---

## 📚 Documentation

For detailed documentation, including API references and advanced usage examples, visit our [documentation site](https://lionfuncs.readthedocs.io).

---

## 🔄 Staying Updated

To stay updated with the latest changes and releases:

1. Watch the [GitHub repository](https://github.com/lion-agi/lionfuncs)
2. Check the [CHANGELOG.md](https://github.com/lion-agi/lionfuncs/blob/main/CHANGELOG.md) for version history
3. Follow us on [Twitter @lionfuncs](https://twitter.com/lionfuncs) for announcements

We follow [Semantic Versioning](https://semver.org/). For upgrade guides between major versions, refer to our documentation.

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](https://github.com/lion-agi/lionfuncs/blob/main/CONTRIBUTING.md) for details on how to get started.

---

## 📄 License

lionfuncs is released under the Apache 2.0 License. See the [LICENSE](https://github.com/lion-agi/lionfuncs/blob/main/LICENSE) file for details.

---

## 🆘 Support

If you encounter any issues or have questions, please file an issue on our [GitHub issue tracker](https://github.com/lion-agi/lionfuncs/issues).

For security-related issues, please refer to our [Security Policy](https://github.com/lion-agi/lionfuncs/security/policy).

---

## 🙏 Acknowledgments

Thank you to all our contributors who've helped make lionfuncs roar! 🦁💖

---

Happy coding with lionfuncs! 🎉👨‍💻👩‍💻
