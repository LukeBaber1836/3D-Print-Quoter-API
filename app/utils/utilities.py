import sys
import time
import shutil
import logging
import subprocess
from stl import mesh
from pathlib import Path
from io import BytesIO
from typing import Union
import aiofiles
from fastapi import UploadFile

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
        printer_dimensions=(210, 210, 250)
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
        model = mesh.Mesh.from_file(Path(stl_file_path))
        
        # Get min and max for x, y, and z
        min_x = float(model.x.min())
        max_x = float(model.x.max())
        min_y = float(model.y.min())
        max_y = float(model.y.max())
        min_z = float(model.z.min())
        max_z = float(model.z.max())
        
        # Calculate dimensions
        dimensions = {
            'x': float(max_x - min_x),
            'y': float(max_y - min_y),
            'z': float(max_z - min_z)
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
                'x': float(printer_dimensions[0]),
                'y': float(printer_dimensions[1]),
                'z': float(printer_dimensions[2])
            },
            'exceeded_dimensions': exceeded_dimensions
        }
    except Exception as e:
        logger.error(f"Error checking STL dimensions: {str(e)}")
        return {'error': f"Failed to analyze STL file: {str(e)}"}


async def convert_path_to_upload_file(file_path: Union[str, Path]) -> UploadFile:
    """
    Convert a local file path to a FastAPI UploadFile object
    
    Args:
        file_path: Path to the file (str or Path object)
        
    Returns:
        UploadFile: A FastAPI UploadFile object
    
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    # Convert to Path object if it's a string
    path = Path(file_path) if isinstance(file_path, str) else file_path
    
    # Check if file exists
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    # Read file content
    async with aiofiles.open(path, 'rb') as f:
        content = await f.read()
    
    # Create file-like object from content
    file_obj = BytesIO(content)
    
    # Create UploadFile
    upload_file = UploadFile(
        filename=path.name,
        file=file_obj
    )
    
    return upload_file


def cleanup_files(user_id: str):
    """
    Clean up temporary files for a user and remove the directory
    
    Args:
        user_id (str): User ID to identify the temporary files
    """
    # Define the directory to clean up
    temp_dir = Path(f"/app/app/db/temp/{user_id}")
    
    # Check if the directory exists
    if temp_dir.exists():
        # Remove the directory and its contents
        shutil.rmtree(temp_dir)


# Define a cleanup function
def cleanup_after_download(user_id: str):
    """Delete a file after it has been downloaded"""
    # Small delay to ensure file has been served
    time.sleep(1)
    
    # Define the directory to clean up
    temp_dir = Path(f"/app/app/db/temp/{user_id}")
    
    # Check if the directory exists
    if temp_dir.exists():
        # Remove the directory and its contents
        shutil.rmtree(temp_dir)


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