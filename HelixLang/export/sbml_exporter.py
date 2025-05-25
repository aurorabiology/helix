import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Optional

SBML_NAMESPACE = "http://www.sbml.org/sbml/level3/version1/core"
ET.register_namespace('', SBML_NAMESPACE)

SUPPORTED_LEVELS = [2, 3]
SUPPORTED_VERSIONS = [1, 2]

class Species:
    def __init__(self, id: str, name: str, initial_concentration: float,
                 compartment: str, boundary_condition: bool):
        self.id = id
        self.name = name
        self.initial_concentration = initial_concentration
        self.compartment = compartment
        self.boundary_condition = boundary_condition

class Parameter:
    def __init__(self, id: str, value: float, constant: bool):
        self.id = id
        self.value = value
        self.constant = constant

class Reaction:
    def __init__(self, id: str, name: str, reactants: Dict[str, float],
                 products: Dict[str, float], kinetic_law: str):
        self.id = id
        self.name = name
        self.reactants = reactants
        self.products = products
        self.kinetic_law = kinetic_law

class Model:
    def __init__(self, id: str, name: str, level: int, version: int,
                 species: List[Species], parameters: List[Parameter],
                 reactions: List[Reaction], annotations: Optional[Dict[str, str]] = None):
        self.id = id
        self.name = name
        self.level = level
        self.version = version
        self.species = species
        self.parameters = parameters
        self.reactions = reactions
        self.annotations = annotations or {}

def xml_escape(text: str) -> str:
    return (text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&apos;"))

def serialize_species(species: Species) -> ET.Element:
    elem = ET.Element("species", {
        "id": species.id,
        "name": species.name,
        "compartment": species.compartment,
        "initialConcentration": str(species.initial_concentration),
        "boundaryCondition": str(species.boundary_condition).lower(),
        "hasOnlySubstanceUnits": "false",
        "constant": "false"
    })
    return elem

def serialize_parameter(param: Parameter) -> ET.Element:
    elem = ET.Element("parameter", {
        "id": param.id,
        "value": str(param.value),
        "constant": str(param.constant).lower()
    })
    return elem

def serialize_species_reference(species_id: str, stoichiometry: float) -> ET.Element:
    return ET.Element("speciesReference", {
        "species": species_id,
        "stoichiometry": str(stoichiometry),
        "constant": "true"
    })

def serialize_reaction(reaction: Reaction) -> ET.Element:
    reaction_elem = ET.Element("reaction", {
        "id": reaction.id,
        "name": reaction.name,
        "reversible": "false",
        "fast": "false"
    })

    list_of_reactants = ET.SubElement(reaction_elem, "listOfReactants")
    for species_id, stoich in reaction.reactants.items():
        list_of_reactants.append(serialize_species_reference(species_id, stoich))

    list_of_products = ET.SubElement(reaction_elem, "listOfProducts")
    for species_id, stoich in reaction.products.items():
        list_of_products.append(serialize_species_reference(species_id, stoich))

    kinetic_law_elem = ET.SubElement(reaction_elem, "kineticLaw")
    math_elem = ET.SubElement(kinetic_law_elem, "math", {
        "xmlns": "http://www.w3.org/1998/Math/MathML"
    })
    # For simplicity, embed kinetic law as text inside math element
    math_elem.text = reaction.kinetic_law

    return reaction_elem

def serialize_annotations(annotations: Dict[str, str]) -> ET.Element:
    annotation_elem = ET.Element("annotation")
    for key, value in annotations.items():
        meta_elem = ET.SubElement(annotation_elem, "meta", {"property": key})
        meta_elem.text = xml_escape(value)
    return annotation_elem

def export_sbml(model: Model) -> str:
    # Basic validation of level and version
    if model.level not in SUPPORTED_LEVELS:
        raise ValueError(f"Unsupported SBML level: {model.level}")
    if model.version not in SUPPORTED_VERSIONS:
        raise ValueError(f"Unsupported SBML version: {model.version}")

    sbml_attrs = {
        "xmlns": SBML_NAMESPACE,
        "level": str(model.level),
        "version": str(model.version)
    }
    sbml_elem = ET.Element("sbml", sbml_attrs)

    model_elem = ET.SubElement(sbml_elem, "model", {
        "id": model.id,
        "name": model.name
    })

    if model.annotations:
        model_elem.append(serialize_annotations(model.annotations))

    list_of_species = ET.SubElement(model_elem, "listOfSpecies")
    for sp in model.species:
        list_of_species.append(serialize_species(sp))

    list_of_parameters = ET.SubElement(model_elem, "listOfParameters")
    for param in model.parameters:
        list_of_parameters.append(serialize_parameter(param))

    list_of_reactions = ET.SubElement(model_elem, "listOfReactions")
    for rxn in model.reactions:
        list_of_reactions.append(serialize_reaction(rxn))

    # Return pretty-printed XML string
    from xml.dom import minidom
    rough_string = ET.tostring(sbml_elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def export_model_to_file(model: Model, filename: str) -> None:
    xml_str = export_sbml(model)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"SBML exported to {filename}")

def example_model() -> Model:
    return Model(
        id="example_model_01",
        name="Simple Gene Regulation",
        level=3,
        version=1,
        species=[
            Species(id="GeneA", name="Gene A", initial_concentration=10.0, compartment="cell", boundary_condition=False),
            Species(id="ProteinA", name="Protein A", initial_concentration=0.0, compartment="cell", boundary_condition=False),
        ],
        parameters=[
            Parameter(id="k_transcription", value=0.5, constant=True),
        ],
        reactions=[
            Reaction(
                id="transcription",
                name="GeneA Transcription",
                reactants={"GeneA": 1.0},
                products={"ProteinA": 1.0},
                kinetic_law="k_transcription * GeneA"
            )
        ],
        annotations={
            "creator": "Python SBML Exporter",
            "created": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    model = example_model()
    export_model_to_file(model, "example_model.sbml")
