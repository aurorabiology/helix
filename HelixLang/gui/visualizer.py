import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QColor
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import glutSolidSphere
import re

# Helper for PDB parsing
def parse_pdb(filename):
    """Minimal PDB parser extracting atom coordinates and types."""
    atoms = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith("ATOM") or line.startswith("HETATM"):
                # Columns based on PDB format
                atom_name = line[12:16].strip()
                residue_name = line[17:20].strip()
                chain_id = line[21].strip()
                residue_seq = int(line[22:26])
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                element = line[76:78].strip()
                atoms.append({
                    "atom_name": atom_name,
                    "residue_name": residue_name,
                    "chain_id": chain_id,
                    "residue_seq": residue_seq,
                    "pos": np.array([x, y, z], dtype=np.float32),
                    "element": element
                })
    return atoms


class MolecularVisualizer(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(800, 600)
        self.atoms = []  # Loaded atoms
        self.atom_colors = {}  # Per atom coloring

        # Camera parameters
        self.zoom = -150.0
        self.rot_x = 0
        self.rot_y = 0
        self.pan_x = 0
        self.pan_y = 0

        # Interaction state
        self.last_mouse_pos = QPoint()
        self.left_button = False
        self.middle_button = False

        # Selected atom index
        self.selected_atom_idx = None

        # OpenGL display lists for performance
        self.sphere_display_list = None

        # For highlighting mutation sites (example)
        self.mutation_sites = set()  # residue_seq indexes

        # Init GLUT (needed for spheres)
        glutInit()

    def load_pdb(self, filename):
        self.atoms = parse_pdb(filename)
        self.selected_atom_idx = None
        self.mutation_sites.clear()
        self.assign_colors()
        self.update()

    def assign_colors(self):
        """Assign colors to atoms based on element or residue or mutation."""
        # Standard CPK colors (simplified)
        cpk_colors = {
            'H': (1.0, 1.0, 1.0),      # white
            'C': (0.3, 0.3, 0.3),      # dark gray
            'N': (0.0, 0.0, 1.0),      # blue
            'O': (1.0, 0.0, 0.0),      # red
            'S': (1.0, 1.0, 0.0),      # yellow
            'P': (1.0, 0.5, 0.0),      # orange
        }
        default_color = (0.5, 0.5, 0.5)
        self.atom_colors = {}
        for i, atom in enumerate(self.atoms):
            if atom["residue_seq"] in self.mutation_sites:
                # Mutation sites colored bright magenta
                self.atom_colors[i] = (1.0, 0.0, 1.0)
            else:
                col = cpk_colors.get(atom["element"], default_color)
                self.atom_colors[i] = col

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.15, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Lighting
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Create display list for sphere (atom)
        self.sphere_display_list = glGenLists(1)
        glNewList(self.sphere_display_list, GL_COMPILE)
        glutSolidSphere(1.0, 20, 20)
        glEndList()

    def resizeGL(self, w, h):
        if h == 0:
            h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, w / h, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera transform
        glTranslatef(self.pan_x / 100.0, -self.pan_y / 100.0, self.zoom)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        # Draw atoms as spheres
        for i, atom in enumerate(self.atoms):
            pos = atom["pos"]
            color = self.atom_colors.get(i, (0.5, 0.5, 0.5))
            if i == self.selected_atom_idx:
                # Highlight selected atom
                glColor3f(1.0, 1.0, 0.0)
                self.draw_sphere(pos, radius=1.5)
            else:
                glColor3f(*color)
                self.draw_sphere(pos, radius=1.0)

        # Draw bonds (optional): could be implemented by distance thresholding

    def draw_sphere(self, position, radius=1.0):
        glPushMatrix()
        glTranslatef(*position)
        glScalef(radius, radius, radius)
        glCallList(self.sphere_display_list)
        glPopMatrix()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()
        if event.button() == Qt.LeftButton:
            self.left_button = True
            self.pick_atom(event.pos())
        elif event.button() == Qt.MiddleButton:
            self.middle_button = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.left_button = False
        elif event.button() == Qt.MiddleButton:
            self.middle_button = False

    def mouseMoveEvent(self, event):
        dx = event.x() - self.last_mouse_pos.x()
        dy = event.y() - self.last_mouse_pos.y()

        if self.left_button:
            self.rot_x += dy
            self.rot_y += dx
        elif self.middle_button:
            self.pan_x += dx
            self.pan_y += dy

        self.last_mouse_pos = event.pos()
        self.update()

    def wheelEvent(self, event):
        # Zoom in/out
        delta = event.angleDelta().y() / 120  # One notch = 120
        self.zoom += delta * 5
        self.zoom = min(max(self.zoom, -500), -10)
        self.update()

    def pick_atom(self, pos):
        """Pick atom on mouse click using color picking technique."""
        # Set up offscreen buffer
        w = self.width()
        h = self.height()
        x = pos.x()
        y = h - pos.y()

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.pan_x / 100.0, -self.pan_y / 100.0, self.zoom)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        glDisable(GL_LIGHTING)
        glDisable(GL_DITHER)

        # Draw each atom with unique color encoding its index
        for i, atom in enumerate(self.atoms):
            color_id = (i + 1)  # 0 reserved for no atom
            r = (color_id & 0xFF) / 255.0
            g = ((color_id >> 8) & 0xFF) / 255.0
            b = ((color_id >> 16) & 0xFF) / 255.0
            glColor3f(r, g, b)
            self.draw_sphere(atom["pos"], radius=1.5)

        glFlush()
        glFinish()

        pixel = glReadPixels(x, y, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
        picked_color = tuple(pixel[0][0])
        picked_id = picked_color[0] + (picked_color[1] << 8) + (picked_color[2] << 16) - 1

        if 0 <= picked_id < len(self.atoms):
            self.selected_atom_idx = picked_id
            print(f"Selected atom: {self.atoms[picked_id]['atom_name']} in residue {self.atoms[picked_id]['residue_name']} {self.atoms[picked_id]['residue_seq']}")
        else:
            self.selected_atom_idx = None

        glEnable(GL_LIGHTING)
        glEnable(GL_DITHER)
        self.update()

    # Hook for dynamic simulation updates
    def update_structure(self, new_atoms):
        """Update atom positions in real time for simulation."""
        self.atoms = new_atoms
        self.assign_colors()
        self.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MolecularVisualizer()
    window.load_pdb("example.pdb")  # Replace with your PDB file path
    window.show()
    sys.exit(app.exec_())
