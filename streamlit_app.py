"""Entry point for Streamlit Community Cloud (expects streamlit_app.py by default)."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "doncaster_dev_app.py"), run_name="__main__")
