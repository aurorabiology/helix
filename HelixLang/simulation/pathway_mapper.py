"""
pathway_mapper.py

HelixLang Pathway Mapper Module

Visualizes biochemical pathways from metabolic and gene regulatory simulation states.
Supports dynamic overlays (flux, expression, mutations) and flexible pathway filtering.

Author: HelixLang Team
Date: 2025-05-24
"""

import networkx as nx
import json
import svgwrite
import logging

logger = logging.getLogger("helixlang.pathway_mapper")


class PathwayMapper:
    """
    Maps and visualizes biochemical pathways from simulation data.
    """

    def __init__(self, visualization_engine):
        """
        Initialize with visualization engine reference.

        Args:
            visualization_engine (object): Reference to visualization_engine.py module.
        """
        self.viz_engine = visualization_engine

        # Graph instance to hold pathway topology
        self.graph = nx.DiGraph()

        # Filters
        self.focus_genes = set()
        self.focus_molecules = set()

        # Overlay data containers
        self.flux_values = {}
        self.gene_expression = {}
        self.mutation_hotspots = {}

    def load_states(self, metabolic_state, grn_state):
        """
        Load current simulation states from metabolic and gene regulatory networks.

        Args:
            metabolic_state (dict): Contains reactions and fluxes.
            grn_state (dict): Contains gene regulatory info and expression levels.
        """
        logger.info("Loading simulation states into pathway mapper")
        self.graph.clear()

        # Add metabolic reactions as edges with flux attributes
        for rxn_id, rxn_data in metabolic_state.get("reactions", {}).items():
            substrates = rxn_data.get("substrates", [])
            products = rxn_data.get("products", [])
            flux = rxn_data.get("flux", 0.0)

            for sub in substrates:
                for prod in products:
                    self.graph.add_edge(sub, prod, reaction=rxn_id, flux=flux, type="metabolic")

            # Store flux for overlays
            self.flux_values[rxn_id] = flux

        # Add gene regulatory network nodes and edges
        for gene_id, gene_data in grn_state.get("genes", {}).items():
            expr = gene_data.get("expression", 0.0)
            regulators = gene_data.get("regulators", [])

            self.graph.add_node(gene_id, type="gene", expression=expr)

            self.gene_expression[gene_id] = expr

            for reg in regulators:
                reg_type = grn_state.get("interactions", {}).get((reg, gene_id), "unknown")
                self.graph.add_edge(reg, gene_id, type="regulatory", regulation=reg_type)

        # Mutation hotspots (optional)
        if "mutation_hotspots" in grn_state:
            self.mutation_hotspots = grn_state["mutation_hotspots"]

    def set_focus(self, genes=None, molecules=None):
        """
        Set filters to focus visualization on specific genes or molecule classes.

        Args:
            genes (list or set): Genes to focus on.
            molecules (list or set): Molecule classes to focus on.
        """
        if genes:
            self.focus_genes = set(genes)
        if molecules:
            self.focus_molecules = set(molecules)

    def _filter_graph(self):
        """
        Filter graph nodes and edges based on focus criteria.

        Returns:
            nx.DiGraph: Filtered subgraph.
        """
        if not self.focus_genes and not self.focus_molecules:
            return self.graph

        filtered_nodes = set()

        for node, attrs in self.graph.nodes(data=True):
            if attrs.get("type") == "gene" and node in self.focus_genes:
                filtered_nodes.add(node)
            elif attrs.get("type") == "metabolite" and node in self.focus_molecules:
                filtered_nodes.add(node)
            # Add additional filters as needed

        return self.graph.subgraph(filtered_nodes).copy()

    def render_graph(self, output_path=None, format="svg"):
        """
        Render the pathway graph with overlays.

        Args:
            output_path (str): File path to save the visualization.
            format (str): Output format ('svg', 'json', etc.).
        """
        filtered_graph = self._filter_graph()

        # Prepare node and edge styles based on overlays
        node_styles = {}
        edge_styles = {}

        # Color code gene expression
        for node, attrs in filtered_graph.nodes(data=True):
            if attrs.get("type") == "gene":
                expr = self.gene_expression.get(node, 0.0)
                node_styles[node] = self._expression_color(expr)
            else:
                node_styles[node] = "#cccccc"  # default color

        # Color code flux on edges
        for u, v, attrs in filtered_graph.edges(data=True):
            if attrs.get("type") == "metabolic":
                flux = attrs.get("flux", 0.0)
                edge_styles[(u, v)] = self._flux_color(flux)
            elif attrs.get("type") == "regulatory":
                edge_styles[(u, v)] = "#0000ff"  # regulatory edges blue

        # Highlight mutation hotspots
        for node, intensity in self.mutation_hotspots.items():
            if node in filtered_graph.nodes:
                node_styles[node] = self._mutation_color(intensity)

        # Use visualization engine to generate output
        if format == "svg":
            svg_data = self.viz_engine.render_svg(filtered_graph, node_styles, edge_styles)
            if output_path:
                with open(output_path, "w") as f:
                    f.write(svg_data)
            else:
                return svg_data
        elif format == "json":
            json_data = self._export_json(filtered_graph, node_styles, edge_styles)
            if output_path:
                with open(output_path, "w") as f:
                    json.dump(json_data, f, indent=2)
            else:
                return json_data
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _expression_color(self, expr_value):
        """
        Map gene expression level to a color gradient.

        Args:
            expr_value (float): Expression level.

        Returns:
            str: Hex color code.
        """
        # Simple gradient: low (blue) to high (red)
        from matplotlib import cm
        norm_expr = min(max(expr_value, 0.0), 1.0)
        color = cm.Reds(norm_expr)
        return self._rgba_to_hex(color)

    def _flux_color(self, flux_value):
        """
        Map flux value to a color intensity.

        Args:
            flux_value (float): Flux magnitude.

        Returns:
            str: Hex color code.
        """
        # Positive flux -> green shades, negative flux -> red shades
        from matplotlib import colors
        max_flux = 10.0  # scaling factor
        norm_flux = max(min(flux_value / max_flux, 1.0), -1.0)

        if norm_flux >= 0:
            rgba = (0, norm_flux, 0, 1)
        else:
            rgba = (-norm_flux, 0, 0, 1)

        return self._rgba_to_hex(rgba)

    def _mutation_color(self, intensity):
        """
        Map mutation hotspot intensity to color.

        Args:
            intensity (float): Mutation intensity.

        Returns:
            str: Hex color code.
        """
        # Strong mutation hotspots colored bright magenta
        base_intensity = min(max(intensity, 0.0), 1.0)
        r = int(255 * base_intensity)
        g = 0
        b = int(255 * (1 - base_intensity))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _rgba_to_hex(self, rgba):
        """
        Convert RGBA tuple (r,g,b,a in 0..1) to hex string.

        Args:
            rgba (tuple): (r, g, b, a)

        Returns:
            str: Hex color string.
        """
        r = int(rgba[0] * 255)
        g = int(rgba[1] * 255)
        b = int(rgba[2] * 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _export_json(self, graph, node_styles, edge_styles):
        """
        Export graph with styling info to JSON format.

        Args:
            graph (nx.DiGraph): Graph to export.
            node_styles (dict): Node color styles.
            edge_styles (dict): Edge color styles.

        Returns:
            dict: JSON-serializable dict representation.
        """
        nodes = []
        for node, attrs in graph.nodes(data=True):
            nodes.append({
                "id": node,
                "type": attrs.get("type", "unknown"),
                "color": node_styles.get(node, "#cccccc"),
                "expression": self.gene_expression.get(node, None)
            })

        edges = []
        for u, v, attrs in graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "type": attrs.get("type", "unknown"),
                "color": edge_styles.get((u, v), "#999999"),
                "reaction": attrs.get("reaction", None),
                "regulation": attrs.get("regulation", None)
            })

        return {
            "nodes": nodes,
            "edges": edges
        }
