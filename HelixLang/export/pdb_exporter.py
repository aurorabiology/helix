import datetime
from typing import List, Optional, Dict, Union

# Constants for PDB fixed-width formatting (atom line)
PDB_ATOM_FORMAT = (
    "ATOM  {atom_serial:5d} {atom_name:^4}{alt_loc:1}{res_name:>3} {chain_id:1}"
    "{res_seq:4d}{i_code:1}   "
    "{x:8.3f}{y:8.3f}{z:8.3f}"
    "{occupancy:6.2f}{temp_factor:6.2f}          "
    "{element:>2}{charge:2}"
)

PDB_HETATM_FORMAT = PDB_ATOM_FORMAT.replace("ATOM", "HETATM")

# Helper classes to represent internal HelixLang protein structure

class Atom:
    def __init__(
        self,
        serial_number: int,
        name: str,
        alt_loc: str,
        res_name: str,
        chain_id: str,
        res_seq: int,
        i_code: str,
        x: float,
        y: float,
        z: float,
        occupancy: float = 1.00,
        temp_factor: float = 0.00,
        element: Optional[str] = None,
        charge: Optional[str] = "  "
    ):
        self.serial_number = serial_number
        self.name = name.strip()
        self.alt_loc = alt_loc if alt_loc else " "
        self.res_name = res_name.strip()
        self.chain_id = chain_id
        self.res_seq = res_seq
        self.i_code = i_code if i_code else " "
        self.x = x
        self.y = y
        self.z = z
        self.occupancy = occupancy
        self.temp_factor = temp_factor
        self.element = element if element else (self.name[0].upper() if self.name else " ")
        self.charge = charge

    def to_pdb_line(self, hetatm: bool = False) -> str:
        fmt = PDB_HETATM_FORMAT if hetatm else PDB_ATOM_FORMAT
        return fmt.format(
            atom_serial=self.serial_number,
            atom_name=self.name,
            alt_loc=self.alt_loc,
            res_name=self.res_name,
            chain_id=self.chain_id,
            res_seq=self.res_seq,
            i_code=self.i_code,
            x=self.x,
            y=self.y,
            z=self.z,
            occupancy=self.occupancy,
            temp_factor=self.temp_factor,
            element=self.element,
            charge=self.charge
        )


class SecondaryStructureElement:
    """
    Represents HELIX or SHEET annotations.
    """
    def __init__(
        self,
        elem_type: str,  # "HELIX" or "SHEET"
        ser_num: int,
        init_res_name: str,
        init_chain_id: str,
        init_seq_num: int,
        init_i_code: str,
        end_res_name: str,
        end_chain_id: str,
        end_seq_num: int,
        end_i_code: str,
        helix_class: Optional[int] = None,  # For helices only
        strand_num: Optional[int] = None,  # For sheets only
        num_strands: Optional[int] = None,  # For sheets only
        comment: Optional[str] = None
    ):
        self.elem_type = elem_type.upper()
        self.ser_num = ser_num
        self.init_res_name = init_res_name
        self.init_chain_id = init_chain_id
        self.init_seq_num = init_seq_num
        self.init_i_code = init_i_code if init_i_code else " "
        self.end_res_name = end_res_name
        self.end_chain_id = end_chain_id
        self.end_seq_num = end_seq_num
        self.end_i_code = end_i_code if end_i_code else " "
        self.helix_class = helix_class
        self.strand_num = strand_num
        self.num_strands = num_strands
        self.comment = comment or ""

    def to_pdb_line(self) -> str:
        if self.elem_type == "HELIX":
            # HELIX record format, fixed width fields
            # https://www.wwpdb.org/documentation/file-format-content/format33/sect5.html#HELIX
            return (
                f"HELIX  {self.ser_num:>3}  "
                f"{self.comment[:3]:<3} "
                f"{self.init_res_name:>3} {self.init_chain_id}{self.init_seq_num:>4}{self.init_i_code} "
                f"{self.end_res_name:>3} {self.end_chain_id}{self.end_seq_num:>4}{self.end_i_code} "
                f"{self.helix_class or 1:>2}                                  "
            )
        elif self.elem_type == "SHEET":
            # SHEET record format
            # https://www.wwpdb.org/documentation/file-format-content/format33/sect5.html#SHEET
            return (
                f"SHEET  {self.ser_num:>3} {self.strand_num:>2} {self.comment[:3]:<3} "
                f"{self.init_res_name:>3} {self.init_chain_id}{self.init_seq_num:>4}{self.init_i_code} "
                f"{self.end_res_name:>3} {self.end_chain_id}{self.end_seq_num:>4}{self.end_i_code} "
                f"{self.num_strands or 1:>2}                                  "
            )
        else:
            return f"# Unknown secondary structure element: {self.elem_type}"

class ProteinModel:
    """
    Represents a single 3D protein conformation, potentially part of an ensemble.
    """
    def __init__(self, model_id: int = 1):
        self.model_id = model_id
        self.atoms: List[Atom] = []
        self.secondary_structures: List[SecondaryStructureElement] = []

    def add_atom(self, atom: Atom):
        self.atoms.append(atom)

    def add_secondary_structure(self, elem: SecondaryStructureElement):
        self.secondary_structures.append(elem)


class PDBExporter:
    """
    Export ProteinModel(s) to PDB format.
    """

    def __init__(self, models: Union[ProteinModel, List[ProteinModel]]):
        if isinstance(models, ProteinModel):
            self.models = [models]
        else:
            self.models = models

    def export(self) -> str:
        """
        Generate full PDB file text for all models.
        """
        pdb_lines = []

        # HEADER record with date and info
        pdb_lines.append(self._generate_header("Generated by HelixLang PDB Exporter"))

        for model in self.models:
            if len(self.models) > 1:
                pdb_lines.append(f"MODEL     {model.model_id}")

            # Secondary structure annotations (HELIX, SHEET)
            for ss in model.secondary_structures:
                pdb_lines.append(ss.to_pdb_line())

            # ATOM/HETATM records
            for atom in model.atoms:
                pdb_lines.append(atom.to_pdb_line())

            if len(self.models) > 1:
                pdb_lines.append("ENDMDL")

        pdb_lines.append("END")

        return "\n".join(pdb_lines)

    def _generate_header(self, desc: str) -> str:
        """
        Generate a PDB HEADER line with description and date.
        """
        date_str = datetime.datetime.now().strftime("%d-%b-%Y").upper()
        desc = desc[:40].upper()
        return f"HEADER    {desc:<40}{date_str:>9}   HELIXLANG"

# Example usage

def example():
    # Create a protein model
    model = ProteinModel(model_id=1)

    # Add atoms: example for one residue (ALA) backbone atoms
    model.add_atom(Atom(
        serial_number=1,
        name="N",
        alt_loc="",
        res_name="ALA",
        chain_id="A",
        res_seq=1,
        i_code="",
        x=11.104,
        y=13.207,
        z=10.678,
        occupancy=1.0,
        temp_factor=20.0,
        element="N"
    ))
    model.add_atom(Atom(
        serial_number=2,
        name="CA",
        alt_loc="",
        res_name="ALA",
        chain_id="A",
        res_seq=1,
        i_code="",
        x=12.560,
        y=13.485,
        z=10.899,
        occupancy=1.0,
        temp_factor=20.0,
        element="C"
    ))
    model.add_atom(Atom(
        serial_number=3,
        name="C",
        alt_loc="",
        res_name="ALA",
        chain_id="A",
        res_seq=1,
        i_code="",
        x=13.111,
        y=12.757,
        z=12.123,
        occupancy=1.0,
        temp_factor=20.0,
        element="C"
    ))
    model.add_atom(Atom(
        serial_number=4,
        name="O",
        alt_loc="",
        res_name="ALA",
        chain_id="A",
        res_seq=1,
        i_code="",
        x=12.457,
        y=12.406,
        z=13.122,
        occupancy=1.0,
        temp_factor=20.0,
        element="O"
    ))

    # Add secondary structure (helix)
    model.add_secondary_structure(SecondaryStructureElement(
        elem_type="HELIX",
        ser_num=1,
        init_res_name="ALA",
        init_chain_id="A",
        init_seq_num=1,
        init_i_code="",
        end_res_name="ALA",
        end_chain_id="A",
        end_seq_num=10,
        end_i_code="",
        helix_class=1,
        comment="H1"
    ))

    exporter = PDBExporter(model)
    pdb_text = exporter.export()
    print(pdb_text)


if __name__ == "__main__":
    example()
