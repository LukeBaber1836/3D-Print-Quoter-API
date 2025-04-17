import sys
import logging
import subprocess
import numpy as np
from stl import mesh
from pathlib import Path

logger = logging.getLogger(__name__)

def get_prusa_print_details(
        gcode_file_path : Path
    ):
    """
    Extract print details like time and filament usage from a G-code file
    
    Args:
        gcode_file_path (str): Path to the G-code file
        
    Returns:
        dict: Dictionary containing print time, filament length, and weight
    """
    details = {
        'filament_length': None,
        'filament_volume': None,
        'filament_weight': None,
        'filament_cost': None,
        'estimated_time': None,
    }
    
    try:
        with open(gcode_file_path, 'r') as file:
            for line in file:
                if line.startswith('; filament used [mm]'):
                    details['filament_length'] = float(line.split('=')[1].strip())

                elif line.startswith('; filament used [cm3]'):
                    details['filament_volume'] = float(line.split('=')[1].strip())

                elif line.startswith('; filament used [g]'):
                    details['filament_weight'] = float(line.split('=')[1].strip())

                elif line.startswith('; total filament cost'):
                    details['filament_cost'] = float(line.split('=')[1].strip())
                
                elif line.startswith('; estimated printing time'):
                    details['estimated_time'] = line.split('=')[1].strip()
                    break # Last line we need, so we can break here        
        return details
    except Exception as e:
        print(f"Error parsing G-code file: {e}")
        return details


def time_str_to_seconds(time_str):
    """
    Convert a time string in format '36m 28s' to total seconds
    
    Args:
        time_str (str): Time string in format 'Xm Ys'
        
    Returns:
        int: Total time in seconds
    """
    # Split by spaces and process each part
    parts = time_str.split()
    seconds = 0
    
    for part in parts:
        if part.endswith('m'):
            seconds += int(part[:-1]) * 60
        elif part.endswith('s'):
            seconds += int(part[:-1])
        elif part.endswith('h'):
            seconds += int(part[:-1]) * 3600
        elif part.endswith('d'):
            seconds += int(part[:-1]) * 86400
            
    return seconds


def check_printability(
        stl_file_path, 
        printer_dimensions=(250, 210, 210)
    ):
    """
    Check if an STL file's dimensions are within the printer's build volume
    
    Args:
        stl_file_path (Path): Path to the STL file to check
        printer_dimensions (tuple): (x, y, z) dimensions of printer build volume in mm
        
    Returns:
        dict: Printability assessment with dimensions and status
    """
    try:         
        # Load the STL file
        model = mesh.Mesh.from_file(str(stl_file_path))
        
        # Get min and max for x, y, and z
        min_x = model.x.min()
        max_x = model.x.max()
        min_y = model.y.min()
        max_y = model.y.max()
        min_z = model.z.min()
        max_z = model.z.max()
        
        # Calculate dimensions
        dimensions = {
            'x': max_x - min_x,
            'y': max_y - min_y,
            'z': max_z - min_z
        }
        
        # Check if dimensions exceed printer capacity
        printable = (
            dimensions['x'] <= printer_dimensions[0] and
            dimensions['y'] <= printer_dimensions[1] and
            dimensions['z'] <= printer_dimensions[2]
        )
        
        # Identify which dimensions exceed the build volume
        exceeded_dimensions = []
        if dimensions['x'] > printer_dimensions[0]:
            exceeded_dimensions.append('x')
        if dimensions['y'] > printer_dimensions[1]:
            exceeded_dimensions.append('y')
        if dimensions['z'] > printer_dimensions[2]:
            exceeded_dimensions.append('z')
            
        return {
            'printable': printable,
            'model_dimensions': dimensions,
            'printer_dimensions': {
                'x': printer_dimensions[0],
                'y': printer_dimensions[1],
                'z': printer_dimensions[2]
            },
            'exceeded_dimensions': exceeded_dimensions
        }
    except ImportError:
        logger.error("numpy-stl package required for STL dimension checking")
        return {'error': "numpy-stl package required for STL dimension checking"}
    except Exception as e:
        logger.error(f"Error checking STL dimensions: {str(e)}")
        return {'error': f"Failed to analyze STL file: {str(e)}"}


def shell(
    command: str, hide_stdout: bool = False, stream: bool = False, **kwargs
) -> list[str]:  # type: ignore
    """
    Runs the command is a fully qualified shell.

    Args:
        command (str): A command.

    Raises:
        OSError: The error cause by the shell.
    """
    process = subprocess.Popen(
        command,
        shell=True,
        universal_newlines=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        **kwargs,
    )

    output = []
    for line in iter(process.stdout.readline, ""):  # type: ignore
        output += [line.rstrip()]
        if not hide_stdout:
            sys.stdout.write(line)
        if stream:
            yield line.rstrip()  # type: ignore

    process.wait()

    if process.returncode != 0:
        raise OSError("\n".join(output))

    return output

def fancy_shell(
    command: str,
    **kwargs,
):
    for line in shell(command, hide_stdout=True, stream=True, **kwargs):
        print(line)