uv add polars-lts-cpu folium pyarrow pandas requests scikit-learn matplotlib

uv run python -m microlog "microlog-example-parent" examples/parent.py
uv run python -m microlog "microlog-example-memory" examples/memory.py
uv run python -m microlog "microlog-example-hello" examples/hello.py
uv run python -m microlog "microlog-example-mp" examples/mp.py
uv run python -m microlog "microlog-example-polars" examples/polars_mapping_example.py
uv run python -m microlog "microlog-example-sklearn" examples/sklearn_classification.py

uv remove polars-lts-cpu folium pyarrow pandas requests scikit-learn matplotlib