#!/bin/bash

LAST=$(find dist -name "*.tar.gz" | sort -V | tail -n 1)

pip install "$LAST" --break-system-packages