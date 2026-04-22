---
tags: [concept, pattern, development-standards, python, aldc]
aliases: [Python style guide, ALDC Python standards]
sources: [Confluence TECH/920616961 (titled "CORE_API" but content is general Python standards), ingested 2026-04-17]
created: 2026-04-17
updated: 2026-04-17
---

# Python Development Standards

ALDC's conventions for writing Python at the company. Applies to any Python codebase in the org — including [[core_api]], [[connector]], and internal tooling.

> The source page on Confluence is titled **"CORE_API"** but its content is general-purpose Python standards, not core_api-specific. Preserved here under a descriptive title.

## Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for code organization and naming.
- **Exception to PEP 8**: spacing around operators.
  - Add a space after commas to avoid crowding.
  - Add single spaces before and after binary operators.
- Use **plural** names for collections, **singular** names for single items.

## Docstrings

Use [Google-style docstrings](https://gist.github.com/redlotus/3bc387c2591e3e908c9b63b97b11d24e).

```python
"""
This is an example of Google docstring style.

Args:
    param1: This is the first param.
    param2: This is a second param.

Returns:
    This is a description of what is returned.

Raises:
    KeyError: Raises an exception.
"""
```

The **first line** should describe the function in a single sentence where possible.

## Tooling

- **Editor**: [VS Code](https://code.visualstudio.com/download)
- **Linter**: [PyLint](https://pylint.pycqa.org/en/latest/) (default) inside VS Code
- **Azure extensions** (official Microsoft) for functionality needed by ALDC's [[Azure]]-hosted services:
  - Azure App Service
  - Azure Databases
  - Azure Functions
  - Azure Resources

## Reading

- [The Zen of Python](https://www.python.org/dev/peps/pep-0020/) — cultural baseline.

## See Also

- [[core_api]] — primary consumer (Python 3.11 + Azure Functions)
- [[connector]] — also Python, follows these standards
- [[Azure]] — the VS Code Azure extensions target this stack
