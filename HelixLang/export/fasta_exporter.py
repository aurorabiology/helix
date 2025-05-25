import re
from typing import List, Optional, Union, Dict

# Valid residue characters for nucleotides and proteins
VALID_NUCLEOTIDES = set("ATUCGN")
VALID_PROTEINS = set(
    "ACDEFGHIKLMNPQRSTVWYBXZJUO"  # Common amino acids + ambiguous codes
)

class Sequence:
    """
    Represents a biological sequence with optional metadata for FASTA export.
    """
    def __init__(self, seq: str, seq_type: str = "nucleotide",
                 header: Optional[str] = None,
                 description: Optional[str] = None,
                 accession: Optional[str] = None):
        self.seq = seq.upper().replace("\n", "").replace(" ", "")
        self.seq_type = seq_type.lower()  # 'nucleotide' or 'protein'
        self.header = header
        self.description = description
        self.accession = accession
        self._validate_sequence()

    def _validate_sequence(self) -> None:
        """
        Validate sequence characters based on type.
        Raises warnings for invalid characters.
        """
        valid_set = VALID_NUCLEOTIDES if self.seq_type == "nucleotide" else VALID_PROTEINS
        invalid_chars = set(self.seq) - valid_set
        if invalid_chars:
            print(f"Warning: Sequence contains invalid characters for {self.seq_type}: "
                  f"{', '.join(sorted(invalid_chars))}")

    def fasta_header(self) -> str:
        """
        Construct a FASTA header line starting with '>'.
        Format: >header [accession] description
        """
        header_parts = []
        if self.header:
            header_parts.append(self.header)
        if self.accession:
            header_parts.append(self.accession)
        if self.description:
            header_parts.append(self.description)
        if not header_parts:
            header_parts.append("unknown_sequence")
        return ">" + " | ".join(header_parts)

def format_sequence(seq: str, line_width: int = 60) -> str:
    """
    Formats sequence string into fixed width lines as per FASTA standard.
    """
    return "\n".join(seq[i:i+line_width] for i in range(0, len(seq), line_width))

def export_fasta(sequences: Union[Sequence, List[Sequence]],
                 filename: Optional[str] = None,
                 line_width: int = 60) -> Optional[str]:
    """
    Export one or more sequences to FASTA format string or write to file.

    Args:
        sequences: Single Sequence or list of Sequence objects.
        filename: If specified, writes output to file.
        line_width: Number of characters per line in sequence.

    Returns:
        FASTA formatted string if filename is None, else None.
    """
    if not isinstance(sequences, list):
        sequences = [sequences]

    fasta_entries = []
    for seq_obj in sequences:
        header = seq_obj.fasta_header()
        formatted_seq = format_sequence(seq_obj.seq, line_width=line_width)
        fasta_entries.append(f"{header}\n{formatted_seq}")

    fasta_str = "\n".join(fasta_entries)

    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(fasta_str)
        print(f"FASTA exported to {filename}")
        return None
    else:
        return fasta_str

# Example Usage / Testing
def example_usage():
    seq1 = Sequence(
        seq="ATGCGTATGCTAGCTAGNNNNATGCTAGCTGATCGT",
        seq_type="nucleotide",
        header="ExampleGene1",
        description="Sample gene sequence",
        accession="XYZ12345"
    )
    seq2 = Sequence(
        seq="MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGE",
        seq_type="protein",
        header="ExampleProtein",
        description="Sample protein sequence"
    )
    fasta_output = export_fasta([seq1, seq2], line_width=70)
    print(fasta_output)

if __name__ == "__main__":
    example_usage()
