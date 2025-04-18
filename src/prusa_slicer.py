import subprocess
import os
import logging
from pathlib import Path
from utilities import (
    fancy_shell, 
    get_prusa_print_details,
    time_str_to_seconds,
    check_printability
)

logger = logging.getLogger(__name__)


class PrusaSlicer:
    def __init__(
        self,
        stl_file_path: Path,  # Path to the STL file
        base_price=5.0,         # Base price for slicing
        cost_per_gram=0.1,      # Cost per gram of filament
        currency="USD",         # Currency for pricing
        cost_per_hour=1.0,      # Cost per hour of printing
        config_path=Path("./configs/config.ini"),       # Path to PrusaSlicer config file
    ):
        """
        Initialize a PrusaSlicer instance with slicing parameters
        
        Args:
            config_path (str, optional): Path to PrusaSlicer config file.
        """
        self.stl_file_path = stl_file_path
        self.base_price = base_price
        self.cost_per_gram = cost_per_gram
        self.currency = currency
        self.cost_per_hour = cost_per_hour
        self.config_path = config_path
        
        # Set executable path based on OS
        if os.name == 'nt':  # Windows
            self.slicer_path = r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe"
            # Check if PrusaSlicer exists at the expected path
            if not os.path.exists(self.slicer_path):
                raise FileNotFoundError(f"PrusaSlicer executable not found at {self.slicer_path}")
            
        else:  # Linux
            self.slicer_path = r"prusa-slicer"
    
        # Parameter to flag mapping
        self.param_flags = {
            'config_path': '--load',
        }

    def slice(
            self,
            stl_file_path : Path = None,
            output_gcode_path : Path = None, 
            **override_params
        ):
        """
        Slice an STL file using PrusaSlicer's command line interface
        
        Args:
            stl_file_path (str): Path to the STL file
            output_gcode_path (str, optional): Path for output G-code file. Defaults to None.
            **override_params: Any parameters to override for this specific slicing operation
            
        Returns:
            bool: True if slicing was successful, False otherwise
        """

        # Build basic command
        if os.name == 'nt':  # Windows
            command = f'"{self.slicer_path}" --export-gcode'
        else:  # Linux
            command = f'{self.slicer_path} --export-gcode'
        
        # Combine default parameters with any overrides
        params = {param: value for param, value in self.__dict__.items() if param in self.param_flags}
        params.update(override_params)
        
        # Add output path if provided
        if output_gcode_path:
            command += f" --output {output_gcode_path}"
        
        # Use object STL file path if not provided
        if stl_file_path is None:
            stl_file_path = self.stl_file_path
            
        # Add parameters to command
        for param, value in params.items():
            if param in self.param_flags and value is not None:
                flag = self.param_flags[param]
                if flag == '--load':
                    command += f' {flag} "{value}"'
                else:
                    command += f" {flag} {value}"
        
        # Add STL file path
        command += f' "{stl_file_path}"'
        
        try:
            # Execute PrusaSlicer
            fancy_shell(command)
            logger.info(f"Slicing completed successfully for {stl_file_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.info(f"Slicing failed: {e}")
            logger.error(f"Error output: {e.stderr}")
            return False

    def quote_price_basic(
            self,
            gcode_file_path: Path = None
        ) -> dict:
        """
        Quote the price of the print based on G-code file
        
        Args:
            gcode_file_path (str): Path to the G-code file
            
        Returns:
            float: Estimated price of the print
        """
        if gcode_file_path is None:
            gcode_file_path = self.stl_file_path.with_suffix('.gcode')

        details = get_prusa_print_details(gcode_file_path=gcode_file_path)
        
        time =  time_str_to_seconds(details['estimated_time']) # Convert estimated time to seconds
        weight = float(details['filament_weight']) # wieght in grams

        total_price = round((self.base_price + (time / 3600) * self.cost_per_hour + (weight * self.cost_per_gram)), 2)

        quote = {
            'total_price': total_price,
            'currency': self.currency,
            'estimated_time': details['estimated_time'],
            'filament_weight': weight,
            'filament_cost': details['filament_cost'],
            'estimated_time_seconds': time,
            'estimate_time': details['estimated_time'],
        }

        return quote


if __name__ == "__main__":
    # Create a slicer with default parameters
    slicer = PrusaSlicer(
        stl_file_path=Path("./stl_files/moon.stl"),
        config_path=Path("./configs/config.ini")
    )
    
    # Slice with default parameters
    checks = check_printability(
        slicer.stl_file_path,
        printer_dimensions=(100, 100, 100),
    )
    
    if checks['printable']:
        slicer.slice()
        quote = slicer.quote_price_basic()
        print(quote)
    else:
        print(f"The STL file is to large to print with the given printer dimensions (mm): X: {checks['printer_dimensions']['x']}, Y: {checks['printer_dimensions']['y']}, Z: {checks['printer_dimensions']['z']}")