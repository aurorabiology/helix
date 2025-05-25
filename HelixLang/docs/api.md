# HelixLang API Reference and Built-in Functions

## Overview

This document provides a comprehensive reference for HelixLang's built-in API, including functions, methods, classes, and standard library modules. It serves as an essential guide for users writing HelixLang scripts and developers extending the language via plugins or custom libraries.

---

## 1. Core API Functions

### 1.1. Sequence Manipulation

| Function            | Signature                          | Description                                           |
|---------------------|----------------------------------|-------------------------------------------------------|
| `concat(seq1, seq2)`| `(Sequence, Sequence) -> Sequence`| Concatenates two sequences (DNA, RNA, or Protein).   |
| `slice(seq, start, end)` | `(Sequence, int, int) -> Sequence` | Extracts a subsequence from `start` to `end` indices.|
| `reverse(seq)`      | `(Sequence) -> Sequence`          | Returns the reverse of the sequence.                  |
| `complement(seq)`   | `(DNASequence) -> DNASequence`    | Computes the complement of a DNA sequence (A<->T, C<->G).|
| `transcribe(dna_seq)` | `(DNASequence) -> RNASequence`  | Transcribes DNA into RNA by replacing T with U.       |
| `translate(rna_seq)` | `(RNASequence) -> ProteinSequence`| Translates RNA codons into a protein amino acid sequence.|

### 1.2. Mutation and Variation

| Function              | Signature                            | Description                                         |
|-----------------------|------------------------------------|---------------------------------------------------|
| `mutate(seq, rate)`   | `(Sequence, float) -> Sequence`    | Introduces random mutations at a specified rate. |
| `induce_mutation(seq, position, new_base)` | `(Sequence, int, char) -> Sequence` | Substitutes base at `position` with `new_base`.  |
| `calculate_mutation_rate(seq1, seq2)` | `(Sequence, Sequence) -> float`   | Calculates the mutation rate between two sequences.|

### 1.3. Protein Folding and Simulation

| Function               | Signature                             | Description                                      |
|------------------------|-------------------------------------|------------------------------------------------|
| `fold_protein(protein_seq)` | `(ProteinSequence) -> ProteinStructure` | Predicts the 3D folded structure of a protein. |
| `simulate_reaction(cell, reaction_params)` | `(Cell, Dict) -> Cell`          | Simulates a chemical reaction inside a cell.    |
| `run_simulation(model, steps)` | `(SimulationModel, int) -> SimulationResult` | Runs a biological simulation for given steps. |

---

## 2. Data Types and Classes

### 2.1. Biological Data Classes

| Class                 | Description                                   | Key Methods/Properties                         |
|-----------------------|-----------------------------------------------|----------------------------------------------|
| `DNASequence`         | Immutable nucleotide sequence (A, T, C, G).   | `.length`, `.complement()`, `.transcribe()` |
| `RNASequence`         | Nucleotide sequence with U instead of T.      | `.length`, `.translate()`                     |
| `ProteinSequence`     | Amino acid sequence representing a protein.  | `.length`, `.fold()`                          |
| `ProteinStructure`    | 3D structural data of folded protein.         | `.get_coordinates()`, `.visualize()`         |
| `Genome`              | Composite structure containing chromosomes.   | `.get_gene(name)`, `.mutate_region(start, end)` |
| `Cell`                | Represents a biological cell with molecules. | `.simulate_step()`, `.get_state()`            |

### 2.2. Standard Container Types

- Lists, dictionaries (maps), and sets support standard operations like indexing, iteration, and mutation.
- Biological sequences implement iterable interfaces.

---

## 3. Standard Library Modules

### 3.1. `genetics.hl`

- Provides utilities for genetic sequence analysis.
- Functions:
  - `gc_content(seq)`: Returns GC content percentage.
  - `find_motifs(seq, motif)`: Finds all occurrences of a motif.
  - `transcribe(seq)`: Converts DNA to RNA.

### 3.2. `protein.hl`

- Functions for protein analysis and modeling.
- Functions:
  - `hydrophobicity(seq)`: Calculates hydrophobic regions.
  - `fold_protein(seq)`: Predicts protein folding.
  - `find_domains(seq)`: Identifies functional protein domains.

---