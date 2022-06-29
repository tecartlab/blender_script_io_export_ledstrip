import bpy
import operator
from mathutils import *
from math import radians

class Exporter:
	
	def __init__( self, config, context ):
		
		self.config = config
		self.context = context
		
		self.log( "ledstrip exporter" )
		self.log( "begin verbose logging..." )
		
		
		# setting up coordinate system
		# SystemMatrix converts from right-handed, z-up to the target coordinate system
		#self.systemMatrix = Matrix()
		#
		#if self.config.coordinateSystem == 'LEFT_HANDED':
		#    self.systemMatrix *= Matrix.Scale( -1, 4, Vector( (0, 0, 1) ) )
		#
		#if self.config.upAxis == 'Y':
		#    self.systemMatrix *= Matrix.Rotation( radians(-90), 4, 'X' )
		
		self.log( "global matrix" )
		self.log( config.global_matrix )
	
	
	def execute( self ):
		
		ledstripXML = ''
		selections = bpy.context.selected_objects
		active_obj = bpy.context.view_layer.objects.active
		
		# ensure Blender is currently in OBJECT mode to allow data access.
		bpy.ops.object.mode_set( mode = 'OBJECT' )
		
		# go through all groups and export all curves alphabetically
		#for obj in selections:
		#	for group in obj.users_group:
		#		objs = []
		#		for obj in group.objects:
		#			if( obj.type == 'CURVE' ):
		#				objs.append( obj )
		#		ledstripXML += self.__export_objs( objs )

		objs = []
		for obj in selections:
			if( obj.type == 'CURVE' ):
				objs.append( obj )
		
		ledstripXML += self.__export_objs( objs )
		
		
		# restore previous selection
		bpy.ops.object.select_all( action='DESELECT' )
		for obj in selections:
			obj.select_set(True)
		bpy.context.view_layer.objects.active = active_obj
		
		# open the file and export XML
		with open( self.config.filepath, 'w' ) as f: # self.filepath, 'w' ) as f:
			f.write( '<ledstrip version="{}">\n'.format( self.config.version ) )
			f.write( ledstripXML )
			f.write( '</ledstrip>\n' )
		
		self.log( "ledstrip exported (%s)" % self.config.filepath, messageVerbose=True )
		
		return True
	
	
	def log( self, string, messageVerbose=False ):
		if self.config.verbose is True or messageVerbose == True:
			print( string )


	def __export_objs( self, objs ):
		
		retXML = ''
		
		objs.sort( key = operator.attrgetter('name'))
		
		for obj in objs:
			self.log( 'converting curve %s' % obj.name )
			self.log( 'location: %s' % obj.location )

			retXML += '\t<segment name="{}">\n'.format( obj.name )
			
			#for spline in obj.data.splines:
			#	self.log(  'number of bezier points: ', len( spline.bezier_points ) )
			#	for point in spline.bezier_points:
			#		self.log(  'coord: ', point.co )
			#		self.log(  'left handle: ', point.handle_left )
			#		self.log( 'right handle: ', point.handle_right )
			#		
			#		frmt = '\t<coord x="{:.2f}" y="{:.2f}" z="{:.2f}"></coord>\n'
			#		ledstripXML += frmt.format( point.co.x, point.co.y, point.co.z )
			
			
			# create mesh out of curve
			bpy.ops.object.select_all( action='DESELECT' ) 
			bpy.context.view_layer.objects.active = obj
			obj.select_set(True)
			
			def0 = obj.data.resolution_u
			def1 = obj.data.fill_mode
			def2 = obj.data.bevel_resolution
			def3 = obj.data.bevel_depth
			
			obj.data.fill_mode = 'FULL'
			obj.data.resolution_u = self.config.resolution
			obj.data.bevel_resolution = 1 #resolution
			obj.data.bevel_depth = 0.0 #thickness
			bpy.ops.object.convert( target='MESH', keep_original=True )
			
			#bpy.ops.group.objects_remove_all()
			
			obj.data.resolution_u = def0
			obj.data.fill_mode = def1           #reverting
			obj.data.bevel_resolution = def2
			obj.data.bevel_depth = def3
			
			
			# apply object transformation (required?)
			#bpy.ops.object.transform_apply( location=True, rotation=True, scale=True )
			
			
			# dump(obj.data)
			newObj = bpy.context.view_layer.objects.active
			mesh = newObj.data
			wm = newObj.matrix_world
			self.log( 'number of vertices=%d' % len( mesh.vertices ) )
			for vert in mesh.vertices:
				co = wm @ vert.co # local to global transform
				cog = self.config.global_matrix @ co # custom transform
				#cog = self.systemMatrix * co
				self.log( 'v %f %f %f' % ( cog.x, cog.y, cog.z ) )
				frmt = '\t\t<coord x="{:.3f}" y="{:.3f}" z="{:.3f}"></coord>\n'
				retXML += frmt.format( cog.x, cog.y, cog.z )
			
			#self.log( 'number of faces=%d' % len( mesh.polygons ) )
			#for face in mesh.polygons:
			#	self.log( 'face' )
			#	for vert in face.vertices:
			#		self.log( vert )
			
			
			# delete temporary mesh object
			bpy.ops.object.delete( use_global=False )
			
			retXML += '\t</segment>\n'
		
		return retXML
