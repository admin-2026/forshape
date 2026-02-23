import FreeCAD as App

from .context import Context
from .exceptions import ShapeException
from .shape import Shape

# script_folder = f'C:/vd/project_random/SynologyDrive/shape_gen_2/shape_gen_2'; sys.path.append(script_folder); from importlib import reload; import shapes.pipe;
# reload(shapes.pipe); from shapes.pipe import Pipe
# Pipe.create_pipe('pipe1', 'profile_sketch', 'spine_sketch')


class Pipe(Shape):
    @staticmethod
    def create_pipe(label, profile_label, spine_label):
        """
        Create a body with an additive pipe by sweeping a profile along a spine.

        Args:
            label (str): Name/label for the pipe object (Body)
            profile_label (str): Label of the existing sketch to use as the cross-section profile
            spine_label (str): Label of the existing sketch to use as the spine/path

        Returns:
            The created or updated Body object
        """
        # Handle incremental build mode
        incremental_build_obj = Shape._incremental_build_if_possible(label)
        if incremental_build_obj is not None:
            return incremental_build_obj

        # Handle teardown mode (sketches are preserved, only pipe is removed)
        if Shape._teardown_if_needed(label, created_children=[label + "_pipe"]):
            return None

        # Check for existing object and get children if they exist
        pipe_label = label + "_pipe"
        existing_obj, children = Shape._get_or_recreate_body(label, [(pipe_label, "PartDesign::AdditivePipe")])

        if existing_obj is not None:
            # Pipe exists, update its properties
            existing_pipe = children[pipe_label]
            needs_recompute = False

            # Update profile
            profile = Context.get_object(profile_label)
            if profile is None:
                raise ShapeException(
                    f"Pipe '{label}' failed: Profile sketch '{profile_label}' not found. "
                    f"Please check that the sketch exists before creating a pipe."
                )

            current_profile = existing_pipe.Profile[0] if existing_pipe.Profile else None
            if current_profile != profile:
                existing_pipe.Profile = (profile, [""])
                needs_recompute = True

            # Update spine
            spine = Context.get_object(spine_label)
            if spine is None:
                raise ShapeException(
                    f"Pipe '{label}' failed: Spine sketch '{spine_label}' not found. "
                    f"Please check that the sketch exists before creating a pipe."
                )

            current_spine = existing_pipe.Spine[0] if existing_pipe.Spine else None
            if current_spine != spine:
                existing_pipe.Spine = (spine, [""])
                needs_recompute = True

            # Hide sketches
            for sketch in [profile, spine]:
                if sketch.Visibility:
                    sketch.Visibility = False
                    needs_recompute = True

            if needs_recompute:
                App.ActiveDocument.recompute()

            return existing_obj

        # Create new object if it doesn't exist
        obj = Shape._create_object(label)

        # Get the profile sketch
        profile = Context.get_object(profile_label)
        if profile is None:
            raise ShapeException(
                f"Pipe '{label}' failed: Profile sketch '{profile_label}' not found. "
                f"Please check that the sketch exists before creating a pipe."
            )

        # Get the spine sketch
        spine = Context.get_object(spine_label)
        if spine is None:
            raise ShapeException(
                f"Pipe '{label}' failed: Spine sketch '{spine_label}' not found. "
                f"Please check that the sketch exists before creating a pipe."
            )

        profile.Visibility = False
        spine.Visibility = False

        # Create pipe
        obj.newObject("PartDesign::AdditivePipe", pipe_label)
        pipe = Context.get_object(pipe_label)
        pipe.Profile = (profile, [""])
        pipe.Spine = (spine, [""])

        App.ActiveDocument.recompute()

        return obj
