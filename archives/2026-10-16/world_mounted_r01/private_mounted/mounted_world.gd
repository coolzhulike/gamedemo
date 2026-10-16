extends 'res://private_inn/world_with_inn.gd'
## New opt-in scene. All inherited world, building, on-foot assets and controller files stay unchanged.
var mount:CharacterBody3D
var baseline_actor:CharacterBody3D
var mounted_camera_angle:=.70
var mounted_camera_distance:=5.8
var mounted_camera_height:=3.1
var mounted_camera_target_height:=1.6
var mounted_camera_smoothing:=true
var mounted_ready:=false
func _ready()->void:
 super._ready()
 baseline_actor=actor;baseline_actor.hide();baseline_actor.collision_layer=0;baseline_actor.collision_mask=0
 mount=load('res://private_mounted/mounted_actor.gd').new();mount.name='MountedCharacterBody';mount.terrain_height=Callable(self,'height_at');add_child(mount)
 actor=mount
 var p:Vector3=inn.to_global(Vector3(13,0,-12));p.y=height_at(p.x,p.z)+.05;mount.position=p
 var d:Vector3=inn.global_basis*Vector3(-1,0,0);mount.facing=atan2(d.x,d.z);mount.rotation.y=mount.facing;yaw=mount.facing-PI
 camera.near=.08;camera.fov=55;camera.current=true
 close_character_camera=true;review_sun.shadow_enabled=true;mounted_ready=true;_mounted_camera(1.0)
 print('MOUNTED_WORLD_READY add_only=true reference_speed_m_s=0.85/3.2 original_on_foot_scene=res://private_inn/main.tscn')
func _physics_process(delta:float)->void:
 if not mounted_ready:return
 elapsed+=delta;wheel_phase=fmod(wheel_phase+delta*.18,TAU)
 for e in wheel_rotors:e.node.basis=e.base*Basis(Vector3.RIGHT,wheel_phase)
 lod_clock+=delta
 if lod_clock>.25:
  lod_clock=0;update_asset_lods();world_terrain.update_lods(camera.global_position);update_groundcover(camera.global_position)
 yaw+=(float(Input.is_physical_key_pressed(KEY_J) or Input.is_key_pressed(KEY_LEFT))-float(Input.is_physical_key_pressed(KEY_L) or Input.is_key_pressed(KEY_RIGHT)))*delta
 mounted_camera_angle+=(float(Input.is_physical_key_pressed(KEY_Q))-float(Input.is_physical_key_pressed(KEY_E)))*delta
 mount.tick(delta,yaw);_mounted_camera(delta)
 status.text='白马骑乘 / 原大世界 + 客栈\nWASD 行走 · Shift 奔跑 · Q/E 绕镜头 · C 远近 · J/L 行进视角\n%s · %.2f m/s · 动画 %.2fx · F1 原走跑跳场景 · H 隐藏说明' % [mount.state,mount.measured_speed,mount.animation_rate]
func _input(event:InputEvent)->void:
 if event is InputEventMouseMotion and Input.mouse_mode==Input.MOUSE_MODE_CAPTURED:
  yaw-=event.relative.x*.003;mounted_camera_height=clampf(mounted_camera_height-event.relative.y*.008,1.7,6)
 if event is InputEventKey and event.pressed and not event.echo:
  if event.keycode==KEY_C:
   close_character_camera=not close_character_camera;mounted_camera_distance=5.8 if close_character_camera else 10.5;mounted_camera_height=3.1 if close_character_camera else 4.7
  elif event.keycode==KEY_F1:get_tree().change_scene_to_file('res://private_inn/main.tscn')
  elif event.keycode==KEY_ESCAPE:Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
  elif event.keycode==KEY_F:Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
  elif event.keycode==KEY_H:status.visible=not status.visible
  elif event.keycode==KEY_F10:get_tree().quit()
func _mounted_camera(delta:float)->void:
 var target:=mount.position+Vector3.UP*mounted_camera_target_height
 var a:float=mount.facing+PI+mounted_camera_angle
 var desired:=mount.position+Vector3(sin(a)*mounted_camera_distance,mounted_camera_height,cos(a)*mounted_camera_distance)
 var query:=PhysicsRayQueryParameters3D.create(target,desired,3,[mount.get_rid(),baseline_actor.get_rid()]);query.hit_from_inside=true
 var hit:=get_world_3d().direct_space_state.intersect_ray(query)
 if not hit.is_empty():desired=hit.position+(target-desired).normalized()*.35
 var probe:=SphereShape3D.new();probe.radius=.25
 var sweep:=PhysicsShapeQueryParameters3D.new();sweep.shape=probe;sweep.transform=Transform3D(Basis.IDENTITY,target);sweep.motion=desired-target;sweep.collision_mask=3;sweep.exclude=[mount.get_rid(),baseline_actor.get_rid()]
 var fractions:=get_world_3d().direct_space_state.cast_motion(sweep)
 if fractions.size()>0 and fractions[0]<1:desired=target+sweep.motion*maxf(.05,fractions[0]-.03)
 camera.position=camera.position.lerp(desired,1-exp(-delta*8)) if mounted_camera_smoothing else desired
 if camera.position.distance_to(target)>.15:camera.look_at(target)
