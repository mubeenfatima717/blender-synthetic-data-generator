import bpy
import sys
import json
import os

# Adding the current directory to sys.path so we can import our core
# This ensures that 'from .. import core' works even in headless mode
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(dir_path)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

import core  # Importing our unified gateway

class HeadlessRunner:
    def __init__(self):
        self.config_path = self.parse_arguments()
        self.config = self.load_config()

    def parse_arguments(self):
        """
        Parses command line arguments. 
        Blender uses '--' to separate Blender args from Python args.
        Example: blender -b -P headless_run.py -- --config my_cfg.json
        """
        if "--config" in sys.argv:
            index = sys.argv.index("--config") + 1
            if index < len(sys.argv):
                return sys.argv[index]
        
        print("ERROR: No configuration file provided. Use --config <path>")
        sys.exit(1)

    def load_config(self):
        """Loads and validates the JSON configuration."""
        if not os.path.exists(self.config_path):
            print(f"ERROR: Config file not found at {self.config_path}")
            sys.exit(1)
        
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def execute(self):
        """
        The main production loop. No Timers, No UI, 100% CPU/GPU utilization.
        """
        print("--- SynthGen Pro: Starting Headless Production ---")
        
        try:
            # 1. Setup Core Engine
            # Note: In headless, we assume the camera name is in the JSON
            cam_name = self.config["annotation_specification"]["target_objects"][0]
            scene_name = bpy.context.scene.name
            
            rand = core.RandomizerEngine(self.config)
            rend = core.RenderController(self.config)
            anno = core.BoundingBoxGenerator(cam_name, scene_name)
            expt = core.FormatPackager(self.config)
            
            rend.setup_engine()
            
            total_images = self.config["randomization_parameters"].get("total_images", 10)
            target_objects = rand.target_objects
            
            # 2. Production Loop
            for i in range(total_images):
                # Randomize
                rand.apply_lighting_randomization()
                for obj in target_objects:
                    rand.apply_random_transform(obj)
                    rand.shuffle_materials(obj)
                
                # Update Scene (Crucial for correct bounding boxes)
                bpy.context.view_layer.update()
                
                # Render
                image_path = rend.render_frame(i)
                
                # Annotate
                frame_labels = []
                for obj in target_objects:
                    bbox = anno.get_2d_bbox(obj)
                    if bbox:
                        label = expt.convert_to_yolo(bbox)
                        frame_labels.append(label)
                
                # Export Label
                if frame_labels:
                    expt.save_label("\n".join(frame_labels), os.path.basename(image_path))
                
                # Progress Reporting for Terminal
                percent = ( (i + 1) / total_images ) * 100
                print(f"[PROGRESS] {i+1}/{total_images} rendered ({percent:.1f}%)")

            print("--- Production Complete: All Data Saved ---")

        except Exception as e:
            print(f"CRITICAL ERROR during execution: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    runner = HeadlessRunner()
    runner.execute()