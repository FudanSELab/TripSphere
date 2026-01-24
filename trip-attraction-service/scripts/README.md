# Trip Attraction Service Scripts

This directory contains scripts for processing and importing attraction data.

## Setup Instructions

### 1. Compile Proto Files
Compile `file.proto` in `contracts/protobuf/` and place the generated code in the `file/` folder.

### 2. Prepare Data Files
Place the `filtered_attractions.json` file in the current directory. The file should contain POI structures provided by AMap (Gaode Maps).

### 3. Organize Image Files
Place image files in the `selected-pictures/{poi_id}/` directories, where `{poi_id}` corresponds to the POI ID.

### 4. Example Files
For examples, please refer to the linked files:https://pan.baidu.com/s/1NiwC9Qq2tbmBGZ-9N1WJcw?pwd=1234

## Usage

```bash
# Run the attraction import script
uv run --script scripts/attraction_info.py
```

## File Structure

```
scripts/
├── README.md                    # This file
├── attraction_info.py          # Main import script
├── file/                       # Generated proto files
│   ├── file_pb2.py
│   └── file_pb2_grpc.py
├── filtered_attractions.json   # POI data (input)
└── selected-pictures/          # Image directories (input)
    └── {poi_id}/
        ├── image1.jpg
        ├── image2.jpg
        └── ...
```

## Requirements

- Python 3.12+
- uv package manager
- Access to MongoDB and file service
