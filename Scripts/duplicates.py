import json

def remove_duplicate_urls(input_filename, output_filename=None):
    """
    Remove duplicate URLs from a JSON file and save the unique URLs to a new file.
    If no output filename is specified, it will append '_unique' to the input filename.
    
    Args:
        input_filename (str): Path to input JSON file containing URLs
        output_filename (str, optional): Path where the unique URLs should be saved
    """
    try:
        # Read the JSON file
        with open(input_filename, 'r') as file:
            urls = json.load(file)
        
        # Remove duplicates while preserving order
        unique_urls = list(dict.fromkeys(urls))
        
        # If no output filename is provided, create one
        if output_filename is None:
            output_filename = input_filename.rsplit('.', 1)[0] + '_unique.json'
        
        # Write the unique URLs back to a file with pretty formatting
        with open(output_filename, 'w') as file:
            json.dump(unique_urls, file, indent=4)
            
        print(f"Successfully removed duplicates!")
        print(f"Original count: {len(urls)}")
        print(f"Unique count: {len(unique_urls)}")
        print(f"Removed {len(urls) - len(unique_urls)} duplicate(s)")
        print(f"Results saved to: {output_filename}")
            
    except FileNotFoundError:
        print(f"Error: Could not find the file '{input_filename}'")
    except json.JSONDecodeError:
        print(f"Error: '{input_filename}' is not a valid JSON file")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
        remove_duplicate_urls(input_file, output_file)
    else:
        print("Usage: python script.py input_file.json [output_file.json]")