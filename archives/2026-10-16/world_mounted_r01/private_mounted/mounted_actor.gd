extends CharacterBody3D
## Additive mounted locomotion. GLB animations are in-place and driven by measured ground travel.
const WALK_SPEED := 0.85
const GALLOP_SPEED := 3.20
var visual:Node3D
var player:AnimationPlayer
var facing:=0.0
var state:="Stand"
var gait:="Walk"
var measured_speed:=0.0
var animation_rate:=0.0
var total_ground_distance:=0.0
var terrain_height:Callable
var before_position:Vector3
var motion_debug:Dictionary={}
var clip_lengths:Dictionary={}
func _ready()->void:
 floor_snap_length=.45;floor_max_angle=deg_to_rad(38);floor_constant_speed=true;safe_margin=.002
 collision_layer=1;collision_mask=3
 # Two conservative vertical capsules cover the horse body; no per-hoof collision claim.
 for z in [-.49,.49]:
  var cs:=CollisionShape3D.new();var shape:=CapsuleShape3D.new();shape.radius=.39;shape.height=1.55;cs.shape=shape;cs.position=Vector3(0,.775,z);add_child(cs)
 visual=load('res://private_mounted/assets/WhiteHorse_Rider_Walk.glb').instantiate();visual.name='HorseAndRider';add_child(visual)
 player=_find_player(visual)
 var walk_name:StringName=''
 for a in player.get_animation_list():
  if a!='RESET':walk_name=a;break
 var walk:Animation=player.get_animation(walk_name).duplicate();walk.loop_mode=Animation.LOOP_LINEAR
 var donor=load('res://private_mounted/assets/WhiteHorse_Rider_Gallop.glb').instantiate()
 var donor_player:AnimationPlayer=_find_player(donor)
 var gallop_name:StringName=''
 for a in donor_player.get_animation_list():
  if a!='RESET':gallop_name=a;break
 var gallop:Animation=donor_player.get_animation(gallop_name).duplicate();gallop.loop_mode=Animation.LOOP_LINEAR
 # Both exports come from the same frozen scene hierarchy and skin. Runtime track paths are checked by QA.
 for name in player.get_animation_library_list():player.remove_animation_library(name)
 var lib:=AnimationLibrary.new();lib.add_animation('Walk',walk);lib.add_animation('Gallop',gallop);player.add_animation_library('',lib)
 clip_lengths={'Walk':walk.length,'Gallop':gallop.length}
 donor.free();player.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
 player.play('Walk');player.advance(0);player.seek(0,true)
 print('MOUNT_CLIPS_READY ',clip_lengths)
func _find_player(node:Node)->AnimationPlayer:
 if node is AnimationPlayer:return node
 for c in node.get_children():
  var p:=_find_player(c)
  if p!=null:return p
 return null
func tick(delta:float,camera_yaw:float)->void:
 var input:=Vector2(float(Input.is_physical_key_pressed(KEY_D))-float(Input.is_physical_key_pressed(KEY_A)),float(Input.is_physical_key_pressed(KEY_S))-float(Input.is_physical_key_pressed(KEY_W)))
 var desired:=Vector3(input.x,0,input.y).rotated(Vector3.UP,camera_yaw).normalized()
 var fast:=Input.is_physical_key_pressed(KEY_SHIFT)
 var commanded_speed:=GALLOP_SPEED if fast else WALK_SPEED
 if desired.length_squared()>.01:
  var target_heading:=atan2(desired.x,desired.z)
  facing=rotate_toward(facing,target_heading,delta*(1.8 if fast else 2.6))
  var forward:=Vector3(sin(facing),0,cos(facing))
  var alignment:=clampf(forward.dot(desired),0.0,1.0)
  var v:=forward*commanded_speed*alignment
  velocity.x=v.x;velocity.z=v.z
 else:velocity.x=move_toward(velocity.x,0,delta*8);velocity.z=move_toward(velocity.z,0,delta*8)
 rotation.y=facing
 if not is_on_floor():velocity.y-=14*delta
 else:velocity.y=-.1
 before_position=position
 move_and_slide()
 var travel:=position-before_position
 measured_speed=Vector2(travel.x,travel.z).length()/delta
 total_ground_distance+=Vector2(travel.x,travel.z).length()
 var next_gait:='Gallop' if fast else 'Walk'
 if next_gait!=gait:
  gait=next_gait;player.play(gait,.22)
 if measured_speed>.015:
  state=gait;animation_rate=measured_speed/(GALLOP_SPEED if gait=='Gallop' else WALK_SPEED)
  player.advance(delta*animation_rate)
 else:state='Stand';animation_rate=0.0
 _align_visual(delta)
 motion_debug={'commanded_speed':commanded_speed if desired.length_squared()>.01 else 0.0,'measured_speed':measured_speed,'gait':gait,'state':state,'animation_rate':animation_rate,'on_floor':is_on_floor(),'floor_normal':str(get_floor_normal()),'clip_position':player.current_animation_position,'slide_collisions':get_slide_collision_count()}
func _align_visual(delta:float)->void:
 if not terrain_height.is_valid():return
 # Visual pitch and roll follow terrain below a hoof-sized footprint. Capsule body still uses move_and_slide.
 var f:=Vector3(sin(facing),0,cos(facing));var r:=Vector3(cos(facing),0,-sin(facing))
 var front:=float(terrain_height.call(position.x+f.x*.85,position.z+f.z*.85))
 var back:=float(terrain_height.call(position.x-f.x*.85,position.z-f.z*.85))
 var right:=float(terrain_height.call(position.x+r.x*.34,position.z+r.z*.34))
 var left:=float(terrain_height.call(position.x-r.x*.34,position.z-r.z*.34))
 var pitch:=clampf(-atan2(front-back,1.7),-.25,.25)
 var roll:=clampf(atan2(right-left,.68),-.20,.20)
 visual.rotation.x=lerp_angle(visual.rotation.x,pitch,1-exp(-delta*10))
 visual.rotation.z=lerp_angle(visual.rotation.z,roll,1-exp(-delta*10))
