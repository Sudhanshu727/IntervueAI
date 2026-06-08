import subprocess
import os
import time
import argparse
import sys
import json
import ast
import re
import threading
from pathlib import Path

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class MemoryMonitor:
    """Monitor peak memory usage during execution"""
    def __init__(self):
        self.peak_memory = 0
        self.monitoring = False
        self.process = None
    
    def start_monitoring(self, process):
        if not PSUTIL_AVAILABLE:
            return
            
        self.process = process
        self.monitoring = True
        self.peak_memory = 0
        self._monitor_thread = threading.Thread(target=self._monitor_memory)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False
        if hasattr(self, '_monitor_thread'):
            self._monitor_thread.join(timeout=1.0)
    
    def _monitor_memory(self):
        while self.monitoring:
            try:
                if self.process and self.process.poll() is None:
                    try:
                        psutil_process = psutil.Process(self.process.pid)
                        memory_info = psutil_process.memory_info()
                        current_memory = memory_info.rss  # RSS memory in bytes
                        self.peak_memory = max(self.peak_memory, current_memory)
                        
                        # Also check child processes
                        for child in psutil_process.children(recursive=True):
                            try:
                                child_memory = child.memory_info().rss
                                self.peak_memory = max(self.peak_memory, current_memory + child_memory)
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                pass
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                time.sleep(0.01)  # Check every 10ms
            except:
                break

def extract_main_function_input(code_content):
    """Extract arguments passed to main function"""
    try:
        tree = ast.parse(code_content)
        main_calls = []
        
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and 
                isinstance(node.func, ast.Name) and 
                node.func.id == 'main'):
                
                args = []
                for arg in node.args:
                    if isinstance(arg, ast.Constant):
                        args.append(repr(arg.value))
                    elif isinstance(arg, ast.Str):  # For older Python versions
                        args.append(repr(arg.s))
                    elif isinstance(arg, ast.Num):  # For older Python versions
                        args.append(str(arg.n))
                    else:
                        try:
                            args.append(ast.unparse(arg) if hasattr(ast, 'unparse') else '<expression>')
                        except:
                            args.append('<expression>')
                
                main_calls.append(args)
        
        return main_calls
    except:
        # Fallback: use regex to find main() calls
        pattern = r'main\s*\(\s*([^)]*)\s*\)'
        matches = re.findall(pattern, code_content)
        result = []
        for match in matches:
            if match.strip():
                # Split by comma and clean up
                args = [arg.strip().strip('"\'') for arg in match.split(',')]
                result.append(args)
            else:
                result.append([])
        return result

def format_memory_usage(bytes_value):
    """Format memory usage in human-readable format"""
    if bytes_value == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def create_test_file_with_input(original_file, test_input_value, language):
    """Create a temporary test file with modified input"""
    if language != 'python':
        return original_file  # Only support Python for now
    
    try:
        with open(original_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the main() call with new input value
        # Look for main(number) pattern and replace the number
        pattern = r'main\s*\(\s*\d+\s*\)'
        new_call = f'main({test_input_value})'
        modified_content = re.sub(pattern, new_call, content)
        
        # If no numeric pattern found, try any main() call
        if modified_content == content:
            pattern = r'main\s*\(\s*[^)]*\s*\)'
            modified_content = re.sub(pattern, new_call, content)
        
        # Create temporary file
        temp_file = original_file.replace('.py', f'_temp_{test_input_value}.py')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        return temp_file
    except Exception as e:
        print(f"Debug: Error creating test file for input {test_input_value}: {e}")
        return original_file

def analyze_time_complexity(code_file_path, language, test_sizes=None):
    """Analyze execution times and memory usage for different input sizes"""
    # Default test input sizes
    if test_sizes is None:
        test_sizes = [10, 100, 1000, 2000, 10000] if language == 'python' else [10, 100, 1000]
    
    execution_times = {}
    memory_usage = {}
    
    print(f"\nRunning tests with input sizes: {test_sizes}")
    print("Note: Large inputs with high complexity algorithms may take a long time...")
    
    for size in test_sizes:
        try:
            # Create test file with this input size
            test_file = create_test_file_with_input(code_file_path, size, language)
            
            if test_file == code_file_path:
                continue
                
            print(f"  Testing n={size}...", end=" ")
            
            # Execute and measure time and memory (multiple runs for better accuracy)
            times_for_size = []
            memory_for_size = []
            
            for run in range(3):  # 3 runs per size
                # Initialize memory monitor
                memory_monitor = MemoryMonitor()
                
                # Start timing
                start_time = time.time()
                
                # Start the process
                process = subprocess.Popen(
                    [sys.executable, test_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Start memory monitoring
                memory_monitor.start_monitoring(process)
                
                # Wait for completion
                try:
                    stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout for larger inputs
                    exit_code = process.returncode
                except subprocess.TimeoutExpired:
                    process.kill()
                    exit_code = -1
                
                # Stop memory monitoring
                memory_monitor.stop_monitoring()
                
                # End timing
                end_time = time.time()
                
                if exit_code == 0:
                    times_for_size.append(end_time - start_time)
                    memory_for_size.append(memory_monitor.peak_memory)
                else:
                    break
            
            if times_for_size and memory_for_size:
                # Use average time and memory for this size
                avg_time = sum(times_for_size) / len(times_for_size)
                avg_memory = sum(memory_for_size) / len(memory_for_size)
                execution_times[size] = round(avg_time, 4)
                memory_usage[size] = int(avg_memory)
                print(f"{avg_time:.4f}s, {format_memory_usage(avg_memory)}")
            else:
                print("failed")
            
            # Clean up temp file
            if test_file != code_file_path:
                try:
                    os.remove(test_file)
                except:
                    pass
                    
        except Exception as e:
            print(f"error: {e}")
            # Clean up temp file on error
            if 'test_file' in locals() and test_file != code_file_path:
                try:
                    os.remove(test_file)
                except:
                    pass
            continue
    
    return {
        "time_measurements": execution_times,
        "memory_measurements": memory_usage
    }

def execute_single_run(code_file_path, language):
    """Single execution run for complexity analysis"""
    abs_code_path = os.path.abspath(code_file_path)
    
    if language == 'python':
        command = [sys.executable, abs_code_path]
    else:
        return {"exit_code": -1}
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5  # Shorter timeout for analysis
        )
        return {"exit_code": result.returncode}
    except:
        return {"exit_code": -1}

def execute_user_code_local(code_file_path, language, custom_test_sizes=None):
    """Execute code locally with enhanced monitoring"""
    abs_code_path = os.path.abspath(code_file_path)
    
    # Read the code to extract main function input
    main_inputs = []
    try:
        with open(abs_code_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        # Extract main function inputs for Python files
        if language == 'python':
            main_inputs = extract_main_function_input(code_content)
    except Exception as e:
        return {
            "main_input": [],
            "output": "",
            "error": f"Could not read file: {str(e)}",
            "exit_code": -1,
            "execution_time": 0,
            "peak_memory": 0,
            "peak_memory_formatted": "0 B"
        }
    
    if language == 'python':
        command = [sys.executable, abs_code_path]
    elif language == 'cpp':
        # For C++, we need to compile first
        exe_path = abs_code_path.replace('.cpp', '.exe').replace('.c', '.exe')
        compile_command = ['g++', abs_code_path, '-o', exe_path]
        
        try:
            # Compile first
            compile_result = subprocess.run(compile_command, capture_output=True, text=True, timeout=30)
            if compile_result.returncode != 0:
                return {
                    "main_input": main_inputs,
                    "output": "",
                    "error": f"Compilation failed:\n{compile_result.stderr}",
                    "exit_code": compile_result.returncode,
                    "execution_time": 0,
                    "peak_memory": 0,
                    "peak_memory_formatted": "0 B"
                }
            command = [exe_path]
        except FileNotFoundError:
            return {
                "main_input": main_inputs,
                "output": "",
                "error": "g++ compiler not found. Please install a C++ compiler.",
                "exit_code": -1,
                "execution_time": 0,
                "peak_memory": 0,
                "peak_memory_formatted": "0 B"
            }
    else:
        return {
            "main_input": main_inputs,
            "output": "",
            "error": "Unsupported language",
            "exit_code": -1,
            "execution_time": 0,
            "peak_memory": 0,
            "peak_memory_formatted": "0 B"
        }

    try:
        # Initialize memory monitor
        memory_monitor = MemoryMonitor()
        
        # Start timing
        start_time = time.time()
        
        # Start the process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Start memory monitoring
        memory_monitor.start_monitoring(process)
        
        # Wait for completion with timeout
        try:
            stdout, stderr = process.communicate(timeout=10)
            exit_code = process.returncode
        except subprocess.TimeoutExpired:
            process.kill()
            memory_monitor.stop_monitoring()
            stdout, stderr = "", "Execution timed out. Possible infinite loop."
            exit_code = -1
        # Stop memory monitoring
        memory_monitor.stop_monitoring()
        
        # End timing
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Analyze execution times for different input sizes if successful
        time_analysis = None
        if exit_code == 0 and language == 'python':
            time_analysis = analyze_time_complexity(abs_code_path, language, custom_test_sizes)
        
        # Clean up exe file if it was created
        if language == 'cpp' and os.path.exists(exe_path):
            try:
                os.remove(exe_path)
            except:
                pass  # Ignore cleanup errors
        
        return {
            "main_input": main_inputs,
            "output": stdout,
            "error": stderr,
            "exit_code": exit_code,
            "execution_time": round(execution_time, 4),
            "peak_memory": memory_monitor.peak_memory,
            "peak_memory_formatted": format_memory_usage(memory_monitor.peak_memory),
            "time_complexity": time_analysis
        }
        
    except Exception as e:
        return {
            "main_input": main_inputs,
            "output": "",
            "error": f"Execution failed: {str(e)}",
            "exit_code": -1,
            "execution_time": 0,
            "peak_memory": 0,
            "peak_memory_formatted": "0 B",
            "time_complexity": None
        }

def validate_file(file_path):
    """Validate if the file exists and has the correct extension"""
    if not os.path.exists(file_path):
        return False, f"File '{file_path}' does not exist."
    
    file_ext = Path(file_path).suffix.lower()
    if file_ext not in ['.py', '.cpp', '.c']:
        return False, f"Unsupported file type '{file_ext}'. Supported types: .py, .cpp, .c"
    
    return True, ""

def determine_language(file_path):
    """Determine the programming language based on file extension"""
    file_ext = Path(file_path).suffix.lower()
    if file_ext == '.py':
        return 'python'
    elif file_ext in ['.cpp', '.c']:
        return 'cpp'
    return None

def format_output(result, verbose=False):
    """Format the execution result for display"""
    print("=" * 60)
    print("ENHANCED CODE EXECUTION RESULTS")
    print("=" * 60)
    
    # Execution status
    if result['exit_code'] == 0:
        print("Status: SUCCESS")
    else:
        print("Status: FAILED")
    
    # Main function input
    if result.get('main_input') and any(result['main_input']):
        print(f"Input to main function: {result['main_input']}")
    else:
        print("Input to main function: No arguments or not detected")
    
    print(f"Time elapsed in running: {result['execution_time']}s")
    
    # Time and memory analysis - show n:time and n:memory dictionaries
    if result.get('time_complexity'):
        analysis_data = result['time_complexity']
        if analysis_data and isinstance(analysis_data, dict):
            if analysis_data.get('time_measurements'):
                print(f"Time analysis (n:time): {analysis_data['time_measurements']}")
            if analysis_data.get('memory_measurements'):
                print(f"Memory analysis (n:bytes): {analysis_data['memory_measurements']}")
        else:
            print("Time and memory analysis: No data available")
    else:
        print("Time and memory analysis: Not performed")
    
    # Memory usage (show even if psutil not available)
    if result.get('peak_memory_formatted'):
        if PSUTIL_AVAILABLE:
            print(f"Peak memory usage: {result['peak_memory_formatted']} ({result['peak_memory']} bytes)")
        else:
            print("Peak memory usage: Not available (install psutil for memory tracking)")
    else:
        print("Peak memory usage: Not available")
    
    print(f"Exit Code: {result['exit_code']}")
    
    # Output section
    print("\n" + "=" * 60)
    print("OUTPUT")
    print("=" * 60)
    if result['output']:
        print(result['output'])
    else:
        print("(No output)")
    
    # Error section
    print("\n" + "=" * 60)
    print("ERROR")
    print("=" * 60)
    if result['error']:
        print(result['error'])
    else:
        print("(No errors)")
    
    print("=" * 60)

def format_json_output(result):
    """Format the execution result as JSON"""
    return json.dumps(result, indent=2)

def get_user_input():
    """Get input from user via interactive menu"""
    print("=" * 60)
    print("ENHANCED CODE EXECUTION ANALYZER")
    print("=" * 60)
    
    # Get file path
    while True:
        file_path = input("\nEnter the path to your Python (.py) or C++ (.cpp/.c) file: ").strip()
        if not file_path:
            print("Please enter a file path.")
            continue
            
        is_valid, error_msg = validate_file(file_path)
        if not is_valid:
            print(f"Error: {error_msg}")
            continue
        
        break
    
    # Get test sizes
    while True:
        print("\nEnter test sizes for complexity analysis.")
        
        test_sizes_input = input("\nEnter test sizes (comma-separated): ").strip()
        
        if not test_sizes_input:
            # Use defaults
            test_sizes = [10, 100, 1000, 2000, 10000]
            print(f"Using default test sizes: {test_sizes}")
            break
        
        try:
            test_sizes = [int(x.strip()) for x in test_sizes_input.split(',')]
            if not test_sizes:
                raise ValueError("No test sizes provided")
            if any(size <= 0 for size in test_sizes):
                raise ValueError("Test sizes must be positive integers")
            print(f"Using test sizes: {test_sizes}")
            break
        except ValueError as e:
            print("Error: Please enter comma-separated positive integers (e.g., '10,50,100')")
            continue
    
    # Ask for output format
    while True:
        output_format = input("\nOutput format - (1) Normal, (2) JSON, (3) Verbose: ").strip()
        if output_format in ['1', '2', '3']:
            break
        print("Please enter 1, 2, or 3")
    
    return file_path, test_sizes, output_format

def main():
    """Main interactive function"""
    try:
        # Get user input
        file_path, test_sizes, output_format = get_user_input()
        
        # Determine language
        language = determine_language(file_path)
        if not language:
            print("Error: Could not determine programming language from file extension.")
            sys.exit(1)
        
        verbose = output_format == '3'
        json_output = output_format == '2'
        
        if verbose:
            print(f"\nExecuting {language.upper()} file: {file_path}")
            print("Mode: LOCAL EXECUTION (no Docker)")
            print(f"Test sizes: {test_sizes}")
            print("-" * 40)
        
        # Execute the code
        result = execute_user_code_local(file_path, language, test_sizes)
        
        # Output results
        if json_output:
            print("\n" + format_json_output(result))
        else:
            print()
            format_output(result, verbose)
            
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()