# Apple Notes to Claude Workflow

This project provides a workflow to:

1. Export Apple Notes content directly from the database as text files
2. Send the text to Claude 3.7 via API for analysis

## Requirements

- macOS (for Apple Notes access)
- Python 3.6+
- Internet connection (for Claude API access)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/apple-notes-orc-flow.git
   cd apple-notes-orc-flow
   ```

2. Run the workflow script, which will automatically:
   - Create a virtual environment (.venv)
   - Install all required dependencies
   ```
   ./run_workflow.sh
   ```

## Usage

Run the workflow with default settings:

```bash
./run_workflow.sh --api-key "your-api-key-here"
```

Or directly:

```bash
./src/workflow.py --api-key "your-api-key-here"
```

### Command-line Options

- `--output-dir`: Directory to store output files (default: ./output)
- `--notes-folder`: Specific Apple Notes folder to process (default: all notes)
- `--claude-prompt`: Prompt to send to Claude along with the extracted text (default: provided in the script)
- `--api-key`: API key for Claude (required)

### Examples

cProcess all notes and save output to a custom directory:
```bash
./run_workflow.sh --api-key "your-api-key-here" --output-dir ~/Documents/notes_analysis
```

Process notes from a specific folder:
```bash
./run_workflow.sh --api-key "your-api-key-here" --notes-folder "Work Notes"
```

Use a custom prompt for Claude:
```bash
./run_workflow.sh --api-key "your-api-key-here" --claude-prompt "Summarize this text in bullet points:"
```


## How It Works

### Step 1: Export Apple Notes Content Directly

The workflow uses AppleScript to:
- Access the Apple Notes SQLite database directly
- Extract note content using SQL queries
- Save the content as text files
- No UI automation or screen recording permissions required

### Step 2: Send to Claude

The workflow sends each text file to Claude 3.7:
- Makes API requests to Claude with the extracted text
- Saves both the full JSON response and the text-only response
- Organizes responses in the output directory

## Output Structure

The workflow creates the following directory structure:

```
output/
├── text/             # Extracted text files directly from Notes database
└── claude_responses/ # Claude API responses
```

## Troubleshooting

### Apple Notes Database Access

- The script accesses the Apple Notes SQLite database directly
- If you encounter permission issues, make sure Terminal/your IDE has full disk access in System Preferences > Security & Privacy > Privacy > Full Disk Access
- If notes aren't exporting correctly, try closing Apple Notes before running the script
- For encrypted notes, the script may not be able to extract the content

### Claude API Issues

- Check your internet connection
- Verify that the API key is correct
- If you're getting rate limit errors, try increasing the delay between requests

## License

MIT
