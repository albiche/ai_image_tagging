## Vision-GPT Beverage Data Extractor

A robust, OpenAI-GPT-powered pipeline to automate structured data extraction and standardization for product images/videos (max 10 images per product), using advanced computer vision, logic rules, and customizable templates.

## 🧩 Project Structure
```
.
├── config/               # Project/configuration and rules
│   ├── conf.yml          # Main pipeline config (model, paths, API key, video setting)
│   ├── logic_rules_npd.yml # YAML file with logical post-processing rules
│   └── template_npd.json   # Template for data extraction (column definitions, prompts)
├── data_filling/
│   ├── models/           # Model abstraction, wrappers, and integrations
│   ├── pipeline/         # Main pipeline scripts (run/test)
│   ├── tools/            # Utility functions for prompt building, normalization, etc.
│   └── utils/            # Global constants and helpers
├── requirements.txt      # Python requirements
├── data/                 # Data not included; see below
```

## Features

### Vision-Language Powered:
- Supports OpenAI vision models (e.g. GPT-4o) for multi-modal understanding
- Handles images and frames from video files (.jpg, .png, .mp4, etc.)

### Customizable Extraction:
- Use a single `template_npd.json` to define all desired fields/columns, accepted values, and individual prompts for each.
- Add/remove fields easily; the pipeline dynamically adapts.

### Intelligent Prompt Splitting:
- Automatically splits large prompts into multiple efficient OpenAI calls, avoiding context/token/image limits.
- Possibility to add a double-check mode, with two tries minimum for each label and a third for conflict resolution.

### Self-Healing + Post-processing:
- Rule-based logic engine (from `logic_rules.yml`) corrects or derives fields, fixes common labeling errors.
- Missing/invalid responses replaced with N/A.
- Output is always in a standardized table.

### Video Support:
- Extracts informative keyframes from videos using either regular interval or dynamic difference-based sampling.

### Simple Pipeline Use:
- Just place your raw media files into `data/cases/[CASE_ID]/` (one folder per product, with images or videos inside).
- Run a single script to fill your database from scratch!

## Installation

### Clone the Repository

### Install Requirements
```bash
pip install -r requirements.txt
```
You'll need system packages for `opencv-python` (for video/image handling).

### Prepare OpenAI API Key

## Usage

### Prepare Your Data
Each CASE should have its own subfolder under `data/cases/[CASE_ID]/`.  
Supported media: `.jpg`, `.jpeg`, `.png`, `.mp4`, `.mov`, `.avi`, `.mkv`, etc.

Example:
```
data/
└── cases/
    └── npd_case/
        ├── product-001/
        │   ├── img1.jpg
        ├── product-002/
        │   ├── img3.jpg
        │   └── img4.jpg
```

### Set/Check Your Config
Edit `config/conf.yml`:
- Choose model (`vision_gpt` recommended)
- Confirm `data_path`, `output_path`, `template_path`, etc.
- If using videos, choose frame extraction mode: `dynamic` (default, best for variety) or `regular`.

### Run the Pipeline
To process all available cases/folders and fill the spreadsheet:
```bash
python data_filling/pipelines/run_from_folder.py
```
**Output**: A CSV file (path as per your config) with one row per case, each column per field (as per template + post-processing logic).

## Advanced Options

- `config/logic_rules_npd.yml`: Contains post-extraction logic (e.g., "If Innovation = No, set Innovation type = No") in YAML.
- `config/template_npd.json`: The master field definition file, with accepted values and prompt for every field. Add or adjust fields here as required.
- `video_frame_strategy`: For controlling how video keyframes are selected: `dynamic` or `regular`.

### Test/Debug Pipeline
For per-case step-through and terminal-friendly display, run:
```bash
python data_filling/pipelines/test.py
```

## Core Logic Flow

1. **Load Configuration & Template**:  
   Read prompt structure, accepted values, fields

2. **Media Loading**:  
   For each case/folder, collect supported image/video files  
   Videos: extract informative frames

3. **Chunked Prompting**:  
   For each case, split fields intelligently across a minimal set of OpenAI API calls  
   (avoid model token/image/execution limits)  
   Send prompts, collect raw JSON answers  
   Retry/fix invalid fields if necessary

4. **Logic Rules**:  
   Apply custom business logic post-processing (from YAML)

5. **Output Normalization & Export**:  
   Fill in any missing fields, ensure 1:1 mapping with template columns  
   Export as CSV (with UTF-8 BOM for Excel compatibility)

## Template & Rules Customization

### Adding/Removing Fields
Edit `config/template_npd.json`:  
Add a new field as a JSON key object with `"prompt_ai"`, `"accepted_values"`, and a unique `"key"` (slug).  
Fields without accepted values or prompt text are filled as `N/A`.

### Changing Data Extraction Logic
Edit/add logic rules in `config/logic_rules_npd.yml`.  
Supported condition styles:  
- If column equals/not-equals/in-list
- `all_of`, `any_of` (for composite rules)

Example:
```yaml
rules:
  - if:
      column: "Innovation"
      equals: "No"
    then:
      set:
        column: "Innovation type"
        value: "No"
```

## Extending & Integrating

- **Model abstraction**: Add new model classes in `data_filling/models/` and register in the `get_model` function.
- **Prompt logic**: Tweak `tools/build_and_split_prompt.py` for chunk/tokens/image limits as needed.
- **Video processing**: Tweak extraction logic in `tools/video_to_frames.py`.

## Supported Formats
- **Images**: `.jpg`, `.jpeg`, `.png`
- **Videos**: `.mp4`, `.mov`, `.avi`, `.mkv`

## Requirements

Python 3.8+, with:

- `openai`
- `opencv-python`
- `pillow`
- `pandas`
- `pyyaml`
- `tiktoken`
- `httpx`

(See `requirements.txt`)

## How It Works (In English)
The pipeline extracts structured marketing/product data for each "case" (product folder) using one or more media files (image/video).  
It leverages GPT-4o's vision capabilities, asking tailored questions for each data field.  
Large templates are split into manageable OpenAI requests, automatically.  
Results are corrected with logical rules (YAML), and always exported to a standardized CSV file.  
Fully customizable and ready to scale for new product types or business logic.

🚩 For more details, see comments in pipeline source code and edit your templates/rules as required for your use case.

## Credits
Developed by AI/ML team, tuned for CPG/Beverage marketing analysis use cases.  
Contributions, bug reports, or feature requests are welcome.

**Security**: Never commit or publish your OpenAI API key!  
**Data**: All extracted data is yours—no information is logged externally by this pipeline.
