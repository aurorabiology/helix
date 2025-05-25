import subprocess
import tempfile
import os
import platform
from helixlang.runtime.value_types import Protein

class ChimeraPlugin:
    def __init__(self, chimera_path=None):
        self.chimera_path = chimera_path or self._detect_chimera_path()
        self.process = None
        self.session_files = []

    def _detect_chimera_path(self):
        if platform.system() == "Windows":
            return r"C:\Program Files\ChimeraX\ChimeraX.exe"
        elif platform.system() == "Darwin":
            return "/Applications/ChimeraX.app/Contents/MacOS/ChimeraX"
        else:
            return "/usr/bin/chimerax"

    def _run_chimera_command(self, command: str):
        # Launch ChimeraX with command argument (non-blocking or blocking as needed)
        full_cmd = [self.chimera_path, "--nogui", "--cmd", command]
        subprocess.run(full_cmd, check=True)

    def visualize_protein(self, protein: Protein):
        # Convert HelixLang Protein to PDB file
        pdb_file = self._export_protein_to_pdb(protein)
        load_command = f"open {pdb_file}; cartoon; color byhet; view"
        self._run_chimera_command(load_command)
        self.session_files.append(pdb_file)

    def _export_protein_to_pdb(self, protein: Protein) -> str:
        # Serialize Protein object to PDB format file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdb")
        with open(temp_file.name, "w") as f:
            f.write(protein.to_pdb_string())  # Assume Protein has this method
        return temp_file.name

    def close(self):
        # Cleanup temporary files
        for f in self.session_files:
            os.unlink(f)
        self.session_files.clear()
