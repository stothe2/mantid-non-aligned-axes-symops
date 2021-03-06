from mantid.kernel import *
from mantid.api import *
from mantid.geometry import *

from collections import defaultdict
from numpy import array
from numpy import dot
from numpy import zeros
from numpy import matrix
from numpy import array_equal


class SpaceGroupSymOps(PythonAlgorithm):

	_binned_ws = None # Output workspace
	symList = ['x,y,z', # Symmetry operation list
		'x,y,-z',
		'x,-y,z',
		'x,-y,-z',
		'-x,y,z',
		'-x,y,-z',
		'-x,-y,z',
		'-x,-y,-z',
		'x,z,y',
		'x,z,-y',
		'x,-z,y',
		'x,-z,-y',
		'-x,z,y',
		'-x,z,-y',
		'-x,-z,y',
		'-x,-z,-y',
		'y,x,z',
		'y,x,-z',
		'y,-x,z',
		'y,-x,-z',
		'-y,x,z',
		'-y,x,-z',
		'-y,-x,z',
		'-y,-x,-z',
		'y,z,x',
		'y,z,-x',
		'y,-z,x',
		'y,-z,-x',
		'-y,z,x',
		'-y,z,-x',
		'-y,-z,x',
		'-y,-z,-x',
		'z,x,y',
		'z,x,-y',
		'z,-x,y',
		'z,-x,-y',
		'-z,x,y',
		'-z,x,-y',
		'-z,-x,y',
		'-z,-x,-y',
		'z,y,x',
		'z,y,-x',
		'z,-y,x',
		'z,-y,-x',
		'-z,y,x',
		'-z,y,-x',
		'-z,-y,x',
		'-z,-y,-x',
		'x,x-y,z',
		'x,x-y,-z',
		'-x,-x+y,z',
		'-x,-x+y,-z',
		'y,-x+y,z',
		'y,-x+y,-z',
		'-y,x-y,z',
		'-y,x-y,-z',
		'x-y,x,z',
		'x-y,x,-z',
		'x-y,-y,z',
		'x-y,-y,-z',
		'-x+y,y,z',
		'-x+y,y,-z',
		'-x+y,-x,z',
		'-x+y,-x,-z']

	def PyInit(self):
		# ------------------------- Input properties -------------------------

		# Space group and symmetry properties
		self.declareProperty('SymmetrizationBy', 'Space Group', validator=StringListValidator(['Space Group', 'Symmetry Operations']))
		self.declareProperty('SpaceGroup', 198, IntBoundedValidator(lower=1, upper=230),
			doc='Space group number as given in International Tables for Crystallography, Vol. A')
		self.declareProperty('Number of symmetry operations', '1', validator=StringListValidator(['1', '2', '3', '4', '5']))

		self.declareProperty('Symmetry operation 1', 'x,y,z', validator=StringListValidator(self.symList))
		self.declareProperty('Symmetry operation 2', 'x,y,z', validator=StringListValidator(self.symList))
		self.declareProperty('Symmetry operation 3', 'x,y,z', validator=StringListValidator(self.symList))
		self.declareProperty('Symmetry operation 4', 'x,y,z', validator=StringListValidator(self.symList))
		self.declareProperty('Symmetry operation 5', 'x,y,z', validator=StringListValidator(self.symList))

		self.setPropertySettings('SpaceGroup', VisibleWhenProperty('SymmetrizationBy', PropertyCriterion.IsEqualTo, 'Space Group'))
		self.setPropertySettings('Number of symmetry operations', VisibleWhenProperty('SymmetrizationBy', PropertyCriterion.IsEqualTo, 'Symmetry Operations'))
		self.setPropertySettings('Symmetry operation 1', VisibleWhenProperty('SymmetrizationBy', PropertyCriterion.IsEqualTo, 'Symmetry Operations'))
		self.setPropertySettings('Symmetry operation 2', VisibleWhenProperty('Number of symmetry operations', PropertyCriterion.IsMoreOrEqual, '2'))
		self.setPropertySettings('Symmetry operation 3', VisibleWhenProperty('Number of symmetry operations', PropertyCriterion.IsMoreOrEqual, '3'))
		self.setPropertySettings('Symmetry operation 4', VisibleWhenProperty('Number of symmetry operations', PropertyCriterion.IsMoreOrEqual, '4'))
		self.setPropertySettings('Symmetry operation 5', VisibleWhenProperty('Number of symmetry operations', PropertyCriterion.IsMoreOrEqual, '5'))

		sym_grp = 'Symmetrization Options'
		self.setPropertyGroup('SymmetrizationBy', sym_grp)
		self.setPropertyGroup('SpaceGroup', sym_grp)
		self.setPropertyGroup('Number of symmetry operations', sym_grp)
		self.setPropertyGroup('Symmetry operation 1', sym_grp)
		self.setPropertyGroup('Symmetry operation 2', sym_grp)
		self.setPropertyGroup('Symmetry operation 3', sym_grp)
		self.setPropertyGroup('Symmetry operation 4', sym_grp)
		self.setPropertyGroup('Symmetry operation 5', sym_grp)

		# Binning properties
		self.declareProperty('AxisAligned', False, 'Perform binning aligned with the axes of the input MDEventWorkspace?')
		self.declareProperty('AlignedDim0', 'h,-3,3,10', StringMandatoryValidator(), 'Format: \'name,limits,bins\'')
		self.declareProperty('AlignedDim1', 'k,-3,3,10', StringMandatoryValidator(), 'Format: \'name,limits,bins\'')
		self.declareProperty('AlignedDim2', 'l,-3,3,1', StringMandatoryValidator(), 'Format: \'name,limits,bins\'')
		self.declareProperty('AlignedDim3', 'E,-3,3,1', StringMandatoryValidator(), 'Format: \'name,limits,bins\'')

		self.declareProperty(FloatArrayProperty(name='OutputBins', values=[50,50,1,1]),
			'The number of bins for each dimension of the OUTPUT workspace')
		self.declareProperty(FloatArrayProperty(name='OutputExtents', values=[-5,5,-5,5,-0.5,0.5,6,10]),
			'The minimum, maximum edges of space of each dimension of the OUTPUT workspace, as a comma-separated list')
		self.declareProperty(FloatArrayProperty(name='Translation',
												values=[0,0,0,0],
												validator=FloatArrayLengthValidator(4)),
			'Coordinates in the INPUT workspace that corresponds to (0,0,0) in the OUTPUT workspace')
		self.declareProperty('Normalise Basis Vectors', True, 'Normalize the given basis vectors to unity')
		self.declareProperty('BasisVector0', 'a,unit,1,1,0,0', 'Format: \'name,units,x,y,z,dE\'. Leave blank for None.')
		self.declareProperty('BasisVector1', 'b,unit,0,0,1,0', 'Format: \'name,units,x,y,z,dE\'. Leave blank for None.')
		self.declareProperty('BasisVector2', 'c,unit,1,-1,0,0', 'Format: \'name,units,x,y,z,dE\'. Leave blank for None.')
		self.declareProperty('BasisVector3', 'E,unit,0,0,0,1', 'Format: \'name,units,x,y,z,dE\'. Leave blank for None.')
		self.declareProperty(WorkspaceProperty(name='InputWorkspace',
												defaultValue='',
												direction=Direction.Input), 'An input MDWorkspace')


		self.setPropertySettings('AlignedDim0',VisibleWhenProperty('AxisAligned', PropertyCriterion.IsNotDefault))
		self.setPropertySettings('AlignedDim1', VisibleWhenProperty('AxisAligned', PropertyCriterion.IsNotDefault))
		self.setPropertySettings('AlignedDim2',VisibleWhenProperty('AxisAligned', PropertyCriterion.IsNotDefault))
		self.setPropertySettings('AlignedDim3', VisibleWhenProperty('AxisAligned', PropertyCriterion.IsNotDefault))
		self.setPropertySettings('OutputBins', EnabledWhenProperty('AxisAligned', PropertyCriterion.IsDefault))
		self.setPropertySettings('OutputExtents', EnabledWhenProperty('AxisAligned', PropertyCriterion.IsDefault))
		self.setPropertySettings('Translation', EnabledWhenProperty('AxisAligned', PropertyCriterion.IsDefault))
		self.setPropertySettings('Normalise Basis Vectors', EnabledWhenProperty('AxisAligned',PropertyCriterion.IsDefault))
		self.setPropertySettings('BasisVector0', VisibleWhenProperty('AxisAligned', PropertyCriterion.IsDefault))
		self.setPropertySettings('BasisVector1', VisibleWhenProperty('AxisAligned', PropertyCriterion.IsDefault))
		self.setPropertySettings('BasisVector2', VisibleWhenProperty('AxisAligned', PropertyCriterion.IsDefault))
		self.setPropertySettings('BasisVector3', VisibleWhenProperty('AxisAligned', PropertyCriterion.IsDefault))

		align_grp = 'Axis-Aligned Binning'
		self.setPropertyGroup('AxisAligned', align_grp)
		self.setPropertyGroup('AlignedDim0', align_grp)
		self.setPropertyGroup('AlignedDim1', align_grp)
		self.setPropertyGroup('AlignedDim2', align_grp)
		self.setPropertyGroup('AlignedDim3', align_grp)

		nonalign_grp = 'Non Axis-Aligned Binning'
		self.setPropertyGroup('OutputBins', nonalign_grp)
		self.setPropertyGroup('OutputExtents', nonalign_grp)
		self.setPropertyGroup('Translation', nonalign_grp)
		self.setPropertyGroup('Normalise Basis Vectors', nonalign_grp)
		self.setPropertyGroup('BasisVector0', nonalign_grp)
		self.setPropertyGroup('BasisVector1', nonalign_grp)
		self.setPropertyGroup('BasisVector2', nonalign_grp)
		self.setPropertyGroup('BasisVector3', nonalign_grp)

		# ------------------------- Output properties ------------------------
		self.declareProperty(WorkspaceProperty(name='Binned Workspace',
												defaultValue='',
												direction=Direction.Output), 'A name for the output MDHistoWorkspace')

	def PyExec(self):
		sgNumber = self.getProperty('SpaceGroup').value
		mdws = self.getProperty('InputWorkspace').value
		Adim0 = self.getProperty('AlignedDim0').value
		Adim1 = self.getProperty('AlignedDim1').value
		Adim2 = self.getProperty('AlignedDim2').value
		Adim3 = self.getProperty('AlignedDim3').value
		basis0 = self.getProperty('BasisVector0').value
		basis1 = self.getProperty('BasisVector1').value
		basis2 = self.getProperty('BasisVector2').value
		basis3 = self.getProperty('BasisVector3').value
		axisAligned = self.getProperty('AxisAligned').value
		normalizeBasisVectors = self.getProperty('Normalise Basis Vectors').value
		outputExtents = self.getProperty('OutputExtents').value
		outputBins = self.getProperty('OutputBins').value
		translation = self.getProperty('Translation').value
		symChoice = self.getProperty('SymmetrizationBy').value
		numOp = self.getProperty('Number of symmetry operations').value
		symOp1 = self.getProperty('Symmetry operation 1').value
		symOp2 = self.getProperty('Symmetry operation 2').value
		symOp3 = self.getProperty('Symmetry operation 3').value
		symOp4 = self.getProperty('Symmetry operation 4').value
		symOp5 = self.getProperty('Symmetry operation 5').value

		# Create a logger to store all errors and other information related to this particular algorithm
		log = Logger("SpaceGroupSymOps_log")

		# Change value of empty basis vectors to None
		if len(basis0) is 0:
			log.fatal("Error: At least one basis vector needs to be defined. Cannot bin!")
		if len(basis1) is 0:
			basis1 = None
		if len(basis2) is 0:
			basis2 = None
		if len(basis3) is 0:
			basis3 = None

		if axisAligned == True:
			translation = [0,0,0,0]
			basis0, extent0, bins0 = self.ConvertToNonAA(Adim0)
			basis1, extent1, bins1 = self.ConvertToNonAA(Adim1)
			basis2, extent2, bins2 = self.ConvertToNonAA(Adim2)
			basis3, extent3, bins3 = self.ConvertToNonAA(Adim3)

			outputExtents = [float(extent0[0]),float(extent0[1]),float(extent1[0]),float(extent1[1]),
			float(extent2[0]),float(extent2[1]), float(extent3[0]),float(extent3[1])]
			outputBins = [int(bins0),int(bins1),int(bins2),int(bins3)]

		self._binned_ws = BinMD(InputWorkspace=mdws, AxisAligned=False,
			BasisVector0=basis0, BasisVector1=basis1,
			BasisVector2=basis2, BasisVector3=basis3,
			NormalizeBasisVectors=normalizeBasisVectors, Translation=translation,
			OutputExtents=outputExtents, OutputBins=outputBins)
		
		if symChoice == "Symmetry Operations":
			self._symmetrize_by_generators(mdws, False, basis0, basis1, basis2, basis3,
				normalizeBasisVectors, translation, outputExtents, outputBins,
				int(numOp), symOp1, symOp2, symOp3, symOp4, symOp5)
		else:
			self._symmetrize_by_sg(mdws, False, basis0, basis1, basis2, basis3,
				normalizeBasisVectors, translation, outputExtents, outputBins,
				sgNumber)
		
		self.setProperty("Binned Workspace", self._binned_ws)


	def category(self):
		return 'PythonAlgorithms'


	def _symmetrize_by_sg(self, mdws, axisAligned, basis0, basis1, basis2, basis3,
		normalizeBasisVectors, translation, outputExtents, outputBins,
		sgNumber):

		hmsymbol = str(SpaceGroupFactory.subscribedSpaceGroupSymbols(sgNumber))[2:-2] #Eliminate quotes and brackets
		sg = SpaceGroupFactory.createSpaceGroup(hmsymbol) 
		pg = PointGroupFactory.createPointGroupFromSpaceGroup(sg)
		symOps = pg.getSymmetryOperations()

		unit0, basisVec0, e0 = self._destringify(basis0)
		unit1, basisVec1, e1 = self._destringify(basis1)
		unit2, basisVec2, e2 = self._destringify(basis2)
		unit3, basisVec3, e3 = self._destringify(basis3)

		numbv = 0
		if basisVec0 is not None:
			BV0prime = self.EquivalentCoordinates(basisVec0,pg,sg)
			numbv +=1
		if basisVec1 is not None:
			BV1prime = self.EquivalentCoordinates(basisVec1,pg,sg)
			numbv +=1
		if basisVec2 is not None:
			BV2prime = self.EquivalentCoordinates(basisVec2,pg,sg)
			numbv +=1
		if basisVec3 is not None:
			BV3prime = self.EquivalentCoordinates(basisVec3,pg,sg)
			numbv +=1

		# Make the arrays of basis vectors into a single 3D array
		if numbv == 4:
			BVprime = array([BV0prime,BV1prime,BV2prime,BV3prime]).transpose(1,0,2)
		elif numbv == 3:
			BVprime = array([BV0prime,BV1prime,BV2prime]).transpose(1,0,2)
		elif numbv == 2:
			BVprime = array([BV0prime,BV1prime]).transpose(1,0,2)
		elif numbv == 1:
			BVprime = array([BV0prime]).transpose(1,0,2)

		# Find the unique sets of basis vectors
		UniqueBasisVecs = self.uniqueBVs(BVprime)

		for BVset in UniqueBasisVecs:
			basisVec0_str = None
			basisVec1_str = None
			basisVec2_str = None
			basisVec3_str = None

			if basisVec0 is not None:
				basisVec0_str = unit0[0] + ',' + unit0[1] + ',' + str(BVset[0,0]) \
					+ ',' + str(BVset[0,1]) + ',' + str(BVset[0,2]) + ',' + e0
			if basisVec1 is not None:
				basisVec1_str = unit1[0] + ',' + unit1[1] + ',' + str(BVset[1,0]) \
					+ ',' + str(BVset[1,1]) + ',' + str(BVset[1,2]) + ',' + e1
			if basisVec2 is not None:
				basisVec2_str = unit2[0] + ',' + unit2[1] + ',' + str(BVset[2,0]) \
					+ ',' + str(BVset[2,1]) + ',' + str(BVset[2,2]) + ',' + e2
			if basisVec3 is not None:
				basisVec3_str = unit3[0] + ',' + unit3[1] + ',' + str(BVset[3,0]) \
					+ ',' + str(BVset[3,1]) + ',' + str(BVset[3,2]) + ',' + e3

			print basisVec0_str
			print basisVec1_str

			self._binned_ws += BinMD(InputWorkspace=mdws, AxisAligned=axisAligned,
				BasisVector0=basisVec0_str, BasisVector1=basisVec1_str,
				BasisVector2=basisVec2_str, BasisVector3=basisVec3_str,
				NormalizeBasisVectors=normalizeBasisVectors, Translation=translation,
				OutputExtents=outputExtents, OutputBins=outputBins)
		
		return

	def EquivalentCoordinates(self,basis,pntgrp,spcgrp):
		"""Generates a list of all equivalent coordinates for a given space group.
		Note that the program assumes that the hkl axes are orthogonal, even if the
		space group is actually triangular or hexagonal"""
		symOps = pntgrp.getSymmetryOperations()

		sgnum = spcgrp.getNumber()
		if sgnum >= 143 and sgnum <= 194:
			print "Triangular/Hexagonal hkl transform"
			CoordTransform = array([[1, -1/(3**0.5), 0], [0, 2/(3**0.5), 0], [0, 0, 1]])
			CoordTransformInverse = array([[1,0.5, 0], [0, (3**0.5)/2, 0], [0, 0, 1]])
		else:
			CoordTransform = array([[1,0, 0], [0, 1, 0], [0, 0, 1]])
			CoordTransformInverse = array([[1,0, 0], [0, 1, 0], [0, 0, 1]])

		# Transform coordinates to non-orthogonal hkl space
		basisprime = dot(CoordTransform, array(basis))
		basisprime = basisprime.tolist()

		EquivCoords = zeros((len(symOps),3)) 
		i = 0
		for item in symOps:
			#Generate symmetry-equivalent coordinates
			coordinatesPrime = item.transformHKL(basisprime)
			EquivCoords[i,0] = coordinatesPrime.X()
			EquivCoords[i,1] = coordinatesPrime.Y()
			EquivCoords[i,2] = coordinatesPrime.Z()
			# Transform back into orthogonal hkl space
			EquivCoords[i] = dot(CoordTransformInverse, EquivCoords[i])
			i+=1
		return EquivCoords

	def uniqueBVs(self, BVs):
		"""Returns the uniqe sets of basis vectors as a single array"""
		UniqueBV = []
		for bv in BVs:
			if not any(array_equal(bv, unique_bv) for unique_bv in UniqueBV):
				UniqueBV.append(bv)
		return UniqueBV

	def _symmetrize_by_generators(self, mdws, axisAligned, basis0, basis1, basis2, basis3,
		normalizeBasisVectors, translation, outputExtents, outputBins,
		numOp, symOp1, symOp2, symOp3, symOp4, symOp5):
		
		unit0, basisVec0, e0 = self._destringify(basis0)
		unit1, basisVec1, e1 = self._destringify(basis1)
		unit2, basisVec2, e2 = self._destringify(basis2)
		unit3, basisVec3, e3 = self._destringify(basis3)

		symOpList = [symOp1, symOp2, symOp3, symOp4, symOp5]
		for i in range(numOp):
			basisVec0_str = None
			basisVec1_str = None
			basisVec2_str = None
			basisVec3_str = None

			symOp = SymmetryOperationFactory.createSymOp(symOpList[i])

			if basisVec0 is not None:
				coordinatesPrime = symOp.transformCoordinates(basisVec0)
				basisVec0_str = unit0[0] + ',' + unit0[1] + ',' + str(coordinatesPrime.getX()) \
							+ ',' + str(coordinatesPrime.getY()) + ',' + str(coordinatesPrime.getZ()) + ',' + e0
			if basisVec1 is not None:
				coordinatesPrime = symOp.transformCoordinates(basisVec1)
				basisVec1_str = unit1[0] + ',' + unit1[1] + ',' + str(coordinatesPrime.getX()) \
							+ ',' + str(coordinatesPrime.getY()) + ',' + str(coordinatesPrime.getZ()) + ',' + e1
			if basisVec2 is not None:
				coordinatesPrime = symOp.transformCoordinates(basisVec2)
				basisVec2_str = unit2[0] + ',' + unit2[1] + ',' + str(coordinatesPrime.getX()) \
							+ ',' + str(coordinatesPrime.getY()) + ',' + str(coordinatesPrime.getZ()) + ',' + e2
			if basisVec3 is not None:
				coordinatesPrime = symOp.transformCoordinates(basisVec3)
				basisVec3_str = unit3[0] + ',' + unit3[1] + ',' + str(coordinatesPrime.getX()) \
							+ ',' + str(coordinatesPrime.getY()) + ',' + str(coordinatesPrime.getZ()) + ',' + e3

			self._binned_ws += BinMD(InputWorkspace=mdws, AxisAligned=axisAligned,
				BasisVector0=basisVec0_str, BasisVector1=basisVec1_str,
				BasisVector2=basisVec2_str, BasisVector3=basisVec3_str,
				NormalizeBasisVectors=normalizeBasisVectors, Translation=translation,
				OutputExtents=outputExtents, OutputBins=outputBins)

		return


	def _destringify(self, basis):
		# Account for empty basis vectors
		if basis is None:
			return None, None, None

		temp = basis.split(',')
		unit = temp[0:2]
		temp = temp[2:]
		return unit, array([int(temp[0]), int(temp[1]), int(temp[2])]), temp[3]


	def ConvertToNonAA(self,AlignedInput):
		if AlignedInput is None:
			return None, 0, 0, 0
		temp = AlignedInput.split(',')
		name = temp[0]
		extent = temp[1:3]
		numbins = temp[3]

		#Build basis vector
		if name == 'h' or name =='H':
			BVect = 'h,rlu,1,0,0,0'
		elif name == 'k' or name =='K':
			BVect = 'k,rlu,0,1,0,0'
		elif name == 'l' or name =='L':
			BVect = 'l,rlu,0,0,1,0'
		elif name == 'E' or name =='DeltaE' or name =='deltaE' or name =='delta E':
			BVect = 'E,eV,0,0,0,1'

		return BVect, extent, numbins


# Register algorithm with Mantid
AlgorithmFactory.subscribe(SymmetrizeBySG)
