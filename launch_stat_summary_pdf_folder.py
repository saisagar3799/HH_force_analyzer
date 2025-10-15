import subprocess
import sys
import os

app_filename = "stat_summary_pdf_folder.py"
os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
subprocess.run([sys.executable, "-m", "streamlit", "run", app_filename])