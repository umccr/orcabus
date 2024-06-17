[build-system]
requires = ["poetry>=1.1.0"]
build-backend = "poetry.masonry.api"

[tool.poetry]
name = "rclone"
version = "0.1.0"
description = "Utility for copying batches of files using rclone"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.9"
# Add any additional dependencies here

[tool.poetry.dev-dependencies]
# Add any development dependencies here

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"