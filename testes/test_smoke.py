# -*- coding: utf-8 -*-
"""Smoke test: garante que o ambiente e os imports base funcionam."""
def test_imports():
    # Importa as dependencias principais; falha = ambiente quebrado.
    import pandas, numpy, openpyxl, folium  # noqa: F401
