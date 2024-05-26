![project's logo](assets/logo.png){ width="300" .center}
# GRAPHEMY
<p align="center">
    <em>Integrating SQLModel and Strawberry, providing a seamless GraphQL integration with Databases easy and fast.</em>
</p>
[![Documentation Status](https://readthedocs.org/projects/graphemy/badge/?version=latest)](https://graphemy.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/MDoreto/graphemy/graph/badge.svg?token=GJDMVBA425)](https://codecov.io/gh/MDoreto/graphemy)
![CI](https://github.com/MDoreto/graphemy/actions/workflows/pipeline.yml/badge.svg)
<a href="https://pypi.org/project/graphemy" target="_blank">
    <img src="https://img.shields.io/pypi/v/graphemy?color=%2334D058&label=pypi%20package" alt="Package version">
</a>


---

**Documentation**: <a href="https://github.com/MDoreto/graphemy" target="_blank">https://github.com/MDoreto/graphemy</a>

**Source Code**: <a href="https://github.com/MDoreto/graphemy" target="_blank">https://github.com/MDoreto/graphemy</a>

---


## Overview

The Graphemy is designed to simplify and streamline the integration of SQLModel and Strawberry in Python projects. This library allows you to create a single class model, which, once declared, automatically provides GraphQL queries via Strawberry. These queries can be easily integrated into a FastAPI backend. All generated routes include filters on all fields, including a custom date filter. Additionally, it facilitates the creation of mutations for data modification and deletion by simply setting a variable in the model. The library also handles table relationships efficiently using Strawberry's dataloaders, providing a significant performance boost. Moreover, it offers a pre-configured authentication setup, which can be configured with just two functions.

## Features

- Integration of SQLModel and Strawberry for GraphQL support.
- Automatic generation of GraphQL queries for FastAPI.
- Powerful filtering capabilities, including custom date filters.
- Effortless creation of mutations for data manipulation.
- Efficient handling of table relationships using Strawberry's dataloaders.
- Pre-configured authentication setup for easy configuration.

{% include "templates/instalation.md" %}