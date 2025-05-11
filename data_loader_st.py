import os

DATA_DIR = "data" # Store constitution files in a 'data' subdirectory

def load_constitution_text(country: str) -> str:
    """
    Loads the constitution text for the selected country from a file.
    Placeholder: You need to create these files and populate them.
    """
    filename = ""
    if country == "Japan":
        filename = "japan_constitution.txt" # Changed from usa_constitution.txt
    elif country == "Monaco":
        filename = "monaco_constitution.txt" # Changed from uk_constitution_summary.txt
    else:
        return "Constitution text not available for this country."

    filepath = os.path.join(DATA_DIR, filename)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.strip(): # Check if file is empty or only whitespace
            return f"The file '{filename}' is empty. Please populate it with the relevant constitutional text."
        return content
    except FileNotFoundError:
        return (f"File '{filename}' not found in the '{DATA_DIR}' directory. "
                f"Please create it and add the constitutional text for {country}.")
    except Exception as e:
        return f"Error loading constitution text for {country}: {e}"

