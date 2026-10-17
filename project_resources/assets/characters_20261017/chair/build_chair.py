import bpy, math, json, os
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name != 'Collection': bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
geo=bpy.data.collections.new('Chair_EditableParts'); scene.collection.children.link(geo)
markers=bpy.data.collections.new('PoseMarkers');scene.collection.children.link(markers)
studio=bpy.data.collections.new('PreviewStudio_NotExported');scene.collection.children.link(studio)

def mat(name, color, rough=.48,metal=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 return m
wood=mat('Walnut_Dark_Heartwood',(.065,.027,.015),.4)
edge=mat('Walnut_Warm_Edges',(.12,.052,.025),.4)
panel=mat('Walnut_Seat_Inset',(.092,.039,.020),.49)
brass=mat('Aged_Brass_Pins',(.25,.17,.065),.34,.65)
parts=[]
def move(obj,col):
 for c in list(obj.users_collection):c.objects.unlink(obj)
 col.objects.link(obj)
def box(name,loc,dim,material=wood,bevel=.004):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=dim
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material);move(o,geo);parts.append(o)
 if bevel:
  mod=o.modifiers.new('Hand_softened_edges','BEVEL');mod.width=bevel;mod.segments=3
  mod=o.modifiers.new('Weighted_corner_normals','WEIGHTED_NORMAL')
 return o
# Ground z=0; front +Y. Real dimensions in metres.
for x in [-.204,.204]:
 for y in [-.204,.204]:
  box(('Rear' if y<0 else 'Front')+('_L' if x<0 else '_R')+'_Leg',(x,y,.204),(.046,.046,.408),wood,.005)
# Seat plane at 0.45. Four framing rails and a slightly recessed broad panel.
box('Seat_Inset',(0,0,.429),(.398,.398,.038),panel,.003)
for x in [-.22,.22]:box('Seat_SideFrame',(x,0,.429),(.040,.480,.042),edge,.004)
for y in [-.22,.22]:box('Seat_EndFrame',(0,y,.429),(.400,.040,.042),edge,.004)
for y in [-.204,.204]:box('Seat_Apron',(0,y,.377),(.365,.028,.060),wood,.005)
for x in [-.204,.204]:box('Side_Apron',(x,0,.377),(.028,.365,.060),wood,.005)
# Low stretchers: side pair, rear; front set lower so calves have room.
for x in [-.204,.204]:box('Side_Stretcher',(x,0,.17),(.024,.367,.027),edge,.004)
box('Rear_Stretcher',(0,-.204,.17),(.367,.024,.027),edge,.004)
box('Front_Stretcher',(0,.204,.12),(.367,.024,.027),edge,.004)
# Open, armless back. Uprights continue the rear legs.
for x in [-.204,.204]:box('Back_Upright',(x,-.211,.669),(.038,.038,.462),wood,.005)
# Gently lifted crest with a continuous shaped silhouette.
xs=[-.266,-.245,-.205,-.14,0,.14,.205,.245,.266]
zs=[.918,.928,.922,.907,.901,.907,.922,.928,.918]
verts=[]
for x,z in zip(xs,zs):
 for y,dz in [(-.240,-.018),(-.200,-.018),(-.240,.018),(-.200,.018)]:verts.append((x,y,z+dz))
faces=[(0,2,3,1)]
for i in range(len(xs)-1):
 a=i*4;b=a+4
 faces += [(a,b,b+1,a+1),(a+2,a+3,b+3,b+2),(a,a+2,b+2,b),(a+1,b+1,b+3,a+3)]
a=(len(xs)-1)*4;faces.append((a,a+1,a+3,a+2))
me=bpy.data.meshes.new('Crest_Sculpted_Profile');me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new('Lifted_Crest_Rail',me);geo.objects.link(o);o.data.materials.append(edge);parts.append(o)
m=o.modifiers.new('Crest_roundover','BEVEL');m.width=.006;m.segments=3;o.modifiers.new('Crest_normals','WEIGHTED_NORMAL')
# Narrow centre back splat, framed rectangular opening and restrained geometric decoration.
box('Back_Centre_Splat',(0,-.214,.676),(.096,.023,.425),panel,.006)
for x in [-.061,.061]:box('Splat_Edge',(x,-.211,.677),(.014,.029,.411),edge,.003)
for z in [.511,.841]:box('Splat_EndCap',(0,-.194,z),(.132,.009,.016),edge,.002)
# Small aged brass square pins, visible from front.
for x in [-.204,.204]:
 for z in [.505,.858]:box('Joinery_Pin',(x,-.190,z),(.009,.003,.009),brass,.001)
# Subtle inset centre motif. No painted decals or texture dependency.
for x in [-.027,.027]:box('Motif_vertical',(x,-.199,.735),(.006,.004,.068),edge,.001)
for z in [.704,.766]:box('Motif_horizontal',(0,-.199,z),(.054,.004,.006),edge,.001)

def marker(name,loc):
 o=bpy.data.objects.new(name,None);markers.objects.link(o);o.location=loc;o.empty_display_type='ARROWS';o.empty_display_size=.09
 return o
marker('SeatSocket',(0,-.025,.45))['meaning']='Seat contact plane, not pelvis bone origin. Forward local +Y in Blender, -Z in Godot.'
marker('GroundOrigin',(0,0,0))
marker('FootTarget_L',(-.105,.36,0));marker('FootTarget_R',(.105,.36,0))
marker('FacingForward',(0,.35,.45))
# Export only asset parts and markers, preserve editable bevels in blend.
bpy.ops.object.select_all(action='DESELECT')
for o in parts+list(markers.objects):o.select_set(True)
bpy.context.view_layer.objects.active=parts[0]
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'wuxia_wood_chair.glb'),export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
# Studio only in .blend, excluded from GLB.
floor=mat('Studio_Stone',(.15,.17,.18),.85)
bpy.ops.mesh.primitive_plane_add(size=200);o=bpy.context.object;o.name='Preview_Floor';o.data.materials.append(floor);move(o,studio)
world=bpy.data.worlds.new('StudioWorld') if not scene.world else scene.world;scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.26,.30,.34,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
for name,loc,power,size in [('Key',(-2,1.5,3),450,2),('Fill',(2,1,2),250,2),('Rim',(0,-2,2.8),600,1.4)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,.5))-o.location).to_track_quat('-Z','Y').to_euler();move(o,studio)
bpy.ops.object.camera_add(location=(1.45,1.8,1.30));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.47))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.32;scene.camera=cam;move(cam,studio)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False
scene.render.resolution_x=1100;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,'wuxia_wood_chair_preview.png')
scene.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'wuxia_wood_chair.blend'))
# Count evaluated mesh triangles.
dg=bpy.context.evaluated_depsgraph_get();tris=0
for o in parts:
 me=o.evaluated_get(dg).to_mesh();me.calc_loop_triangles();tris+=len(me.loop_triangles);o.evaluated_get(dg).to_mesh_clear()
json.dump({'triangles':tris,'editable_parts':len(parts),'seat_height_m':.45,'seat_width_m':.48,'seat_depth_m':.48,'overall_width_m':.532,'overall_height_m':.946,'blender_forward':'+Y','godot_forward':'-Z','godot_seat_socket':[0,.45,.025]},open(os.path.join(OUT,'asset_stats.json'),'w'),indent=2)
bpy.ops.render.render(write_still=True)
print('CHAIR_BUILD_DONE')
