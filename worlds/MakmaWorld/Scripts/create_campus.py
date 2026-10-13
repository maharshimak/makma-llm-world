"""Run using UnrealEditor-Cmd -ExecutePythonScript to create the actual .umap.

Uses only engine starter primitives. This is an architectural blockout, not
finished environmental art. No third-party assets or inference in the editor.
"""
import json
from pathlib import Path
import unreal

project=Path(unreal.Paths.project_dir())
spec=json.loads((project/"ContentSource/campus.json").read_text(encoding="utf-8"))
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
levels.new_level("/Game/Maps/Campus")
cube=unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
cylinder=unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
sphere=unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")

def mesh(name,position,scale,asset=cube):
    actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*position))
    actor.set_actor_label(name)
    component=actor.static_mesh_component
    component.set_static_mesh(asset)
    component.set_mobility(unreal.ComponentMobility.STATIC)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor

def label(text,x,y,z):
    actor=actors.spawn_actor_from_class(unreal.TextRenderActor,unreal.Vector(x,y,z),unreal.Rotator(0,-90,0))
    component=actor.get_component_by_class(unreal.TextRenderComponent)
    component.set_text(text)
    component.set_world_size(45)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    return actor

mesh("Campus ground",(0,1300,-55),(190,125,1))
mesh("Central pedestrian spine",(0,0,-2),(185,16,.06))
mesh("Campus road",(0,-4200,-2),(185,10,.06))
mesh("Road sidewalk",(0,-3500,0),(185,3,.08))
mesh("North path",(0,4200,0),(180,3,.08))
for x in [-6500,-3300,0,3300,6500]:
    mesh("Accessible north-south path",(x,1000,0),(3,100,.08))
for entry in spec:
    name,x,y,w,h,interior=entry["name"],entry["x"],entry["y"],entry["half_width"],entry["half_depth"],entry["interior"]
    if not interior:
        label(name,x,y,80)
        if entry["id"]=="park":
            for dx,dy in [(-650,300),(650,300),(-650,-300),(650,-300)]:
                mesh("Tree trunk",(x+dx,y+dy,120),(.5,.5,2.4),cylinder)
                mesh("Tree canopy",(x+dx,y+dy,330),(2.5,2.5,3),sphere)
        continue
    mesh(name+" floor",(x,y,0),(w*2/100,h*2/100,.1))
    mesh(name+" north wall",(x,y+h,190),(w*2/100,.2,3.8))
    mesh(name+" west wall",(x-w,y,190),(.2,h*2/100,3.8))
    mesh(name+" east wall",(x+w,y,190),(.2,h*2/100,3.8))
    # A 300 cm entrance remains physically open; no door teleports.
    segment=(w-150)/100
    mesh(name+" entrance left",(x-(w+150)/2,y-h,190),(segment,.2,3.8))
    mesh(name+" entrance right",(x+(w+150)/2,y-h,190),(segment,.2,3.8))
    mesh(name+" lintel",(x,y-h,330),(3,.2,1.2))
    label(name,x,y-h-20,430)
    # Roof-free blockout makes the occupied interior readable to the observer camera.
    for i in range(8 if entry["id"] in {"ai_lab","systems_lab","apartments","university"} else 3):
        ox=x+(i%4-1.5)*240;oy=y+(i//4)*240
        mesh("Desk",(ox+85,oy,70),(1.1,1.5,.12))
        mesh("Desk support",(ox+85,oy,35),(.2,1,.7))
        mesh("Workstation screen",(ox+110,oy,105),(.08,.8,.5))
        mesh("Chair seat",(ox,oy,40),(.45,.45,.1))
        mesh("Chair support",(ox,oy,20),(.1,.1,.4))
sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,2000),unreal.Rotator(-35,25,0))
sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,500))
actors.spawn_actor_from_class(unreal.SkyAtmosphere,unreal.Vector(0,0,0))
actors.spawn_actor_from_class(unreal.ExponentialHeightFog,unreal.Vector(0,0,-50))
start=actors.spawn_actor_from_class(unreal.PlayerStart,unreal.Vector(0,-700,150))
start.set_actor_label("Player arrival — campus plaza")
nav=actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume,unreal.Vector(0,1000,150))
nav.set_actor_scale3d(unreal.Vector(100,70,12))
levels.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True,True)
unreal.log("MAKMA_CAMPUS_CREATED: /Game/Maps/Campus; build navigation and playtest required")
