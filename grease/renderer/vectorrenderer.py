
from grease.geometry import Vec2d
import ctypes
from math import sin, cos, radians
import pyglet


class VectorRenderer(object):
	"""Renders shapes in vector graphics style"""

	CORNER_FILL_SCALE = 0.6
	CORNER_FILL_THRESHOLD = 2.0

	def __init__(self, scale=1.0, line_width=None, corner_fill=True,
		position_component='position', 
		renderable_component='renderable', 
		shape_component='shape'):
		"""Initialize a vector renderer

		scale -- Scaling factor applied to shape vertices when rendered.
	
		line_width -- The line width provided to glLineWidth before rendering.
		If not specified or None, glLineWidth is not called, and the line
		width used is determined by the OpenGL state at the time of rendering.

		corner_fill -- If true (the default), the shape corners will be filled
		with round points when the line_width exceeds 2.0. This improves
		the visual quality of the rendering at larger line widths at some
		cost to performance. Has no effect if line_width is not specified.

		position_component -- Name of Position component to use. Shapes rendered
		are offset by the entity positions.

		renderable_component -- Name of Renderable component to use. This component
		specifies the entities to be rendered and their base color.

		shape_component -- Name of shape component to use. Source of the shape
		vertices for each entity.

		The entities rendered are taken from the intersection of he position,
		renderable and shape components each time draw() is called.
		"""
		self.scale = float(scale)
		self.corner_fill = corner_fill
		self.line_width = line_width
		self._max_line_width = None
		self.position_component = position_component
		self.renderable_component = renderable_component
		self.shape_component = shape_component
	
	def set_world(self, world):
		self.world = world

	def _generate_verts(self):
		"""Generate vertex and index arrays for rendering"""
		vert_count = sum(len(shape.verts) + 1
			for shape, ignored, ignored in self.world.components.join(
				self.shape_component, self.position_component, self.renderable_component))
		v_array = (CVertColor * vert_count)()
		if vert_count > 65536:
			i_array = (ctypes.c_uint * 2 * vert_count)()
			i_size = pyglet.gl.GL_UNSIGNED_INT
		else:
			i_array = (ctypes.c_ushort * (2 * vert_count))()
			i_size = pyglet.gl.GL_UNSIGNED_SHORT
		v_index = 0
		i_index = 0
		scale = self.scale
		rot_vec = Vec2d(0, 0)
		for shape, position, renderable in self.world.components.join(
			self.shape_component, self.position_component, self.renderable_component):
			shape_start = v_index
			angle = radians(-position.angle)
			rot_vec.x = cos(angle)
			rot_vec.y = sin(angle)
			r = int(renderable.color.r * 255)
			g = int(renderable.color.g * 255)
			b = int(renderable.color.b * 255)
			a = int(renderable.color.a * 255)
			for vert in shape.verts:
				vert = vert.cpvrotate(rot_vec) * scale + position.xy
				v_array[v_index].vert.x = vert.x
				v_array[v_index].vert.y = vert.y
				v_array[v_index].color.r = r
				v_array[v_index].color.g = g
				v_array[v_index].color.b = b
				v_array[v_index].color.a = a
				if v_index > shape_start:
					i_array[i_index] = v_index - 1
					i_index += 1
					i_array[i_index] = v_index
					i_index += 1
				v_index += 1
			if shape.closed and v_index - shape_start > 2:
				i_array[i_index] = v_index - 1
				i_index += 1
				i_array[i_index] = shape_start
				i_index += 1
		return v_array, i_size, i_array, i_index

	def draw(self, gl=pyglet.gl):
		"""Render the entities"""
		vertices, index_size, indices, index_count = self._generate_verts()
		gl.glPushClientAttrib(gl.GL_CLIENT_VERTEX_ARRAY_BIT)
		gl.glEnableClientState(gl.GL_VERTEX_ARRAY)
		gl.glEnableClientState(gl.GL_COLOR_ARRAY)
		gl.glVertexPointer(2, gl.GL_FLOAT, ctypes.sizeof(CVertColor), ctypes.pointer(vertices))
		gl.glColorPointer(
			4, gl.GL_UNSIGNED_BYTE, ctypes.sizeof(CVertColor), ctypes.pointer(vertices[0].color))
		if self.line_width is not None:
			gl.glLineWidth(self.line_width)
			if self._max_line_width is None:
				range_out = (ctypes.c_float * 2)()
				gl.glGetFloatv(gl.GL_ALIASED_LINE_WIDTH_RANGE, range_out)
				self._max_line_width = float(range_out[1]) * self.CORNER_FILL_SCALE
			if self.corner_fill and self.line_width > self.CORNER_FILL_THRESHOLD:
				gl.glEnable(gl.GL_POINT_SMOOTH)
				gl.glPointSize(min(self.line_width * self.CORNER_FILL_SCALE, self._max_line_width))
				gl.glDrawArrays(gl.GL_POINTS, 0, index_count)
		gl.glDrawElements(gl.GL_LINES, index_count, index_size, ctypes.pointer(indices))
		gl.glPopClientAttrib()


class CVert(ctypes.Structure):
	_fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

class CColor(ctypes.Structure):
	_fields_ = [
		("r", ctypes.c_ubyte), ("g", ctypes.c_ubyte), ("b", ctypes.c_ubyte), ("a", ctypes.c_ubyte)]

class CVertColor(ctypes.Structure):
	_fields_ = [("vert", CVert), ("color", CColor)]

