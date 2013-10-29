"""
TransformationList

:Authors:
	Berend Klein Haneveld
"""
from vtk import vtkTransform
from vtk import vtkMatrix4x4
from PySide.QtCore import QObject
from PySide.QtCore import Signal
from Transformation import Transformation
from core.vtkObjectWrapper import vtkTransformWrapper


class TransformationList(QObject):
	"""
	TransformationList that serves as a list of vtkTransform objects.
	By querying a certain index it will return a vtkTransform that is
	a concatination of all transforms up to (and including) that index.
	"""
	transformationChanged = Signal(object)

	def __init__(self):
		super(TransformationList, self).__init__()

		self._transformations = []
		self._cachedTransformation = None
		self._dirty = True

	def completeTransform(self):
		"""
		Use this function instead of transformationList[-1] to get
		a cached version of the complete transformation matrix.
		"""
		if self._dirty:
			self._cachedTransformation = self.transform(len(self._transformations))
			self._dirty = False
		return self._cachedTransformation

	def copyFromTransformations(self, other):
		self._transformations = []
		for transformation in other._transformations:
			self._transformations.append(transformation)
		self._dirty = True
		self.transformationChanged.emit(self)

	def scalingTransform(self):
		"""
		For now, just return the complete transformation.
		It is a very complex problem to remove rotation from
		a transformation matrix that requires another more
		sophisticated solution.
		"""
		transform = self.completeTransform()
		return transform

	def transform(self, index):
		tempTransform = vtkTransform()
		tempTransform.PostMultiply()
		for transformation in self._transformations[0:index]:
			tempTransform.Concatenate(transformation.transform)

		matrix = vtkMatrix4x4()
		matrix.DeepCopy(tempTransform.GetMatrix())
		
		result = vtkTransform()
		result.SetMatrix(matrix)
		return result

	# Methods for loading and saving to file

	def getPythonVersion(self):
		"""
		Returns an object that can be written to file by
		yaml. It creates a list of tuples where each tuple
		consists out of the transformation type and a wrapped
		vtkTransform.
		"""
		result = []
		for transformation in self._transformations:
			# First wrap the transform
			wrappedTransform = vtkTransformWrapper(transformation.transform)
			# Create a tuple
			wrappedTransformation = (transformation.transformType, wrappedTransform)
			# Add the tuple to the results
			result.append(wrappedTransformation)
		return result

	def setPythonVersion(self, transformWrappers):
		self._transformations = []
		self._dirty = True

		for wrappedTransformation in transformWrappers:
			# Get the transform type
			transformType = wrappedTransformation[0]
			# Get the wrapped transform and unwrap immediately
			transform = wrappedTransformation[1].originalObject()
			# Add the transform to the internal transformations
			self._transformations.append(Transformation(transform, transformType))

		self.transformationChanged.emit(self)

	# Override methods for list behaviour

	def __getitem__(self, index):
		return self._transformations[index]

	def __setitem__(self, index, value):
		assert type(value) == Transformation
		self._transformations[index] = value
		self._dirty = True
		self.transformationChanged.emit(self)

	def __delitem__(self, index):
		del self._transformations[index]
		self._dirty = True
		self.transformationChanged.emit(self)

	def __len__(self):
		return len(self._transformations)

	def __contains__(self, value):
		return value in self._transformations

	def append(self, value):
		"""
		:type value: Transformation
		"""
		assert type(value) == Transformation
		self._transformations.append(value)
		self._dirty = True
		self.transformationChanged.emit(self)