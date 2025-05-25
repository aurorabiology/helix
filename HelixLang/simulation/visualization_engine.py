"""
visualization_engine.py

HelixLang Visualization Engine Module

Provides interfaces between simulation results and rendering backends
supporting multi-modal 2D/3D visualizations, user interactivity,
streaming large data, and plugin extensibility.

Author: HelixLang Team
Date: 2025-05-24
"""

import logging
import threading
from collections import deque
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
import numpy as np
import json

logger = logging.getLogger("helixlang.visualization_engine")


class VisualizationEngine:
    def __init__(self):
        # Rendering backends registry (e.g., WebGL, matplotlib, VTK)
        self.backends = {
            "matplotlib_2d": self._render_matplotlib_2d,
            "matplotlib_3d": self._render_matplotlib_3d,
            # "webgl": self._render_webgl,  # placeholder for WebGL backend
            # "vtk": self._render_vtk,      # placeholder for VTK backend
        }

        # Loaded plugins (user-defined visualization modules)
        self.plugins = {}

        # Streaming queue for large datasets
        self._stream_queue = deque()
        self._stream_thread = None
        self._streaming_active = False

        # Scene state for zoom/pan/selection
        self._scene_state = {
            "zoom_level": 1.0,
            "pan_offset": (0, 0),
            "selected_objects": set(),
            "annotations": [],
        }

        logger.info("VisualizationEngine initialized")

    def register_plugin(self, name, plugin_callable):
        """
        Register a custom visualization plugin.

        Args:
            name (str): Plugin identifier.
            plugin_callable (callable): Function/class handling visualization.
        """
        self.plugins[name] = plugin_callable
        logger.info(f"Registered plugin: {name}")

    def unregister_plugin(self, name):
        """Remove a registered plugin by name."""
        if name in self.plugins:
            del self.plugins[name]
            logger.info(f"Unregistered plugin: {name}")

    def render_svg(self, graph, node_styles, edge_styles):
        """
        Render a networkx graph to SVG using matplotlib.

        Args:
            graph (nx.Graph): Graph to render.
            node_styles (dict): Node colors.
            edge_styles (dict): Edge colors.

        Returns:
            str: SVG string of rendered graph.
        """
        import io
        import networkx as nx

        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(graph)  # force-directed layout

        # Draw nodes with colors
        node_colors = [node_styles.get(node, "#cccccc") for node in graph.nodes()]
        nx.draw_networkx_nodes(graph, pos, node_color=node_colors, node_size=300)

        # Draw edges with colors
        edge_colors = [edge_styles.get(edge, "#999999") for edge in graph.edges()]
        nx.draw_networkx_edges(graph, pos, edge_color=edge_colors)

        # Draw labels
        nx.draw_networkx_labels(graph, pos, font_size=8)

        # Save to SVG string buffer
        buf = io.StringIO()
        plt.savefig(buf, format="svg")
        plt.close()
        svg_data = buf.getvalue()
        buf.close()
        logger.info("Rendered graph to SVG")
        return svg_data

    def _render_matplotlib_2d(self, data, **kwargs):
        """
        Render 2D visualizations using matplotlib.

        Args:
            data (dict): Visualization data.

        Returns:
            matplotlib.figure.Figure: Rendered figure.
        """
        fig, ax = plt.subplots()
        ax.plot(data.get("x", []), data.get("y", []), **kwargs)
        ax.set_title(data.get("title", "2D Visualization"))
        logger.info("Rendered 2D matplotlib visualization")
        return fig

    def _render_matplotlib_3d(self, data, **kwargs):
        """
        Render 3D visualizations using matplotlib.

        Args:
            data (dict): Visualization data.

        Returns:
            matplotlib.figure.Figure: Rendered figure.
        """
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        x = data.get("x", [])
        y = data.get("y", [])
        z = data.get("z", [])
        ax.scatter(x, y, z, **kwargs)
        ax.set_title(data.get("title", "3D Visualization"))
        logger.info("Rendered 3D matplotlib visualization")
        return fig

    def render(self, data, backend="matplotlib_2d", **kwargs):
        """
        Generic rendering interface.

        Args:
            data (dict): Visualization data.
            backend (str): Backend name.

        Returns:
            Depends on backend.
        """
        if backend not in self.backends:
            logger.error(f"Unsupported backend: {backend}")
            raise ValueError(f"Unsupported backend: {backend}")

        logger.info(f"Rendering with backend: {backend}")
        return self.backends[backend](data, **kwargs)

    def stream_data(self, data_generator, callback, backend="matplotlib_2d", **kwargs):
        """
        Stream large datasets for rendering in background thread.

        Args:
            data_generator (generator): Yields visualization data chunks.
            callback (callable): Called with each rendered frame.
            backend (str): Backend to use.
        """
        if self._streaming_active:
            logger.warning("Stream already active")
            return

        self._streaming_active = True

        def stream_worker():
            for data_chunk in data_generator:
                if not self._streaming_active:
                    break
                fig = self.render(data_chunk, backend=backend, **kwargs)
                callback(fig)
            self._streaming_active = False
            logger.info("Streaming ended")

        self._stream_thread = threading.Thread(target=stream_worker)
        self._stream_thread.start()
        logger.info("Started streaming thread")

    def stop_streaming(self):
        """
        Stop active streaming visualization.
        """
        self._streaming_active = False
        if self._stream_thread:
            self._stream_thread.join()
        logger.info("Stopped streaming")

    # User interactivity APIs

    def zoom(self, factor):
        """
        Zoom in/out the visualization scene.

        Args:
            factor (float): Zoom multiplier.
        """
        self._scene_state["zoom_level"] *= factor
        logger.info(f"Zoom level changed to {self._scene_state['zoom_level']}")

    def pan(self, dx, dy):
        """
        Pan the visualization scene.

        Args:
            dx (float): X-axis pan delta.
            dy (float): Y-axis pan delta.
        """
        x, y = self._scene_state["pan_offset"]
        self._scene_state["pan_offset"] = (x + dx, y + dy)
        logger.info(f"Panned to {self._scene_state['pan_offset']}")

    def select_objects(self, object_ids):
        """
        Select objects in the visualization.

        Args:
            object_ids (iterable): IDs of selected objects.
        """
        self._scene_state["selected_objects"].update(object_ids)
        logger.info(f"Selected objects: {self._scene_state['selected_objects']}")

    def annotate(self, annotation_text, position):
        """
        Add an annotation to the scene.

        Args:
            annotation_text (str): Annotation content.
            position (tuple): Coordinates for annotation.
        """
        self._scene_state["annotations"].append({"text": annotation_text, "pos": position})
        logger.info(f"Added annotation at {position}: {annotation_text}")

    # Placeholder for future WebGL or VTK implementations
    # def _render_webgl(self, data, **kwargs): ...
    # def _render_vtk(self, data, **kwargs): ...
