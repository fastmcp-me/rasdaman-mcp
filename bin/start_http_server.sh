#!/bin/bash

.venv/bin/python src/main.py --transport http --port 8000 --host 0.0.0.0 --rasdaman-url "http://localhost:8080/rasdaman/ows"
