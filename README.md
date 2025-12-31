# Video Workflow Automation Script

[🇰🇷 한국어 문서](README%20(한국어).md)

An automated workflow script designed to manage large video files with state tracking, automatic copying, and Discord notifications. While originally created for YouTube upload workflows, this versatile tool can be adapted for various media management purposes.

## 📋 Table of Contents
- [Overview](#overview)
- [Use Cases](#use-cases)
- [Key Features](#key-features)
- [Installation & Configuration](#installation--configuration)
- [Usage](#usage)
- [Status Lifecycle](#status-lifecycle)
- [Configuration Reference](#configuration-reference)
- [License](#license)

## Overview

This Python-based automation script monitors a source directory for large video files, automatically copies them to a target directory, tracks their processing state using an SQLite database, and optionally sends summary reports via Discord webhooks. The system is ideal for NAS environments like Synology, but can be used on any Linux-based system.

## Use Cases

This script can be adapted for multiple purposes:

### 1. **YouTube Upload Workflow** (Primary Use Case)
Automatically prepare video files for YouTube upload by copying them to an upload staging area, tracking upload progress, and managing completed uploads.

### 2. **Large File Backup Automation**
Monitor a directory for large video files and automatically copy them to backup storage, maintaining a complete audit trail of all backup operations.

### 3. **Video Processing Pipeline**
Set up a multi-stage video processing workflow where files move through different directories as they progress through editing, rendering, and publishing stages.

### 4. **Media Archive Management**
Organize and track large media files as they move from active storage to archive storage, with automatic detection and status tracking.

### 5. **Cloud Storage Sync Preparation**
Prepare large video files for cloud uploads by staging them in a sync folder, tracking which files have been successfully synced.

### 6. **Content Distribution Workflow**
Manage content distribution by automatically copying finished videos to distribution folders and tracking which platforms have received each file.

## Key Features

- **Automatic File Discovery**: Scans source directory for video files meeting size criteria (default: 100MB+)
- **Configurable File Types**: Supports custom file extensions (`.mp4`, `.mov`, `.avi`, etc.)
- **State Management**: SQLite database tracks file status throughout the workflow
- **History Tracking**: Complete audit trail of all state changes with timestamps
- **Automatic Directory Creation**: Creates required directories if they don't exist
- **Discord Integration**: Optional webhook notifications for daily summary reports
- **Error Handling**: Robust error handling with detailed logging
- **Scheduler Ready**: Designed to run via cron or task scheduler

## Installation & Configuration

### Prerequisites
- Python 3.x
- Bash shell (for Linux/Unix systems)
- SQLite3 (usually included with Python)

### Step 1: Download the Project
Clone or download this repository to your system.

### Step 2: Configure Settings
1. Rename `config(base).json` to `config.json`
2. Edit `config.json` with your specific paths and settings:

```json
{
    "source_dir": "/path/to/source/folder",
    "upload_dir": "/path/to/target/folder",
    "completed_dir": "/path/to/completed/folder",
    "db_path": "/path/to/database/video_workflow.db",
    "min_size_mb": 100,
    "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
    "extensions": [".mp4", ".mov", ".MP4", ".MOV"]
}
```

**Configuration Options:**
- `source_dir`: Directory to monitor for new video files
- `upload_dir`: Target directory where files will be copied
- `completed_dir`: Directory where processed files are moved
- `db_path`: Path to SQLite database file
- `min_size_mb`: Minimum file size in MB to process (default: 100)
- `webhook_url`: Discord webhook URL for notifications (optional)
- `extensions`: List of file extensions to monitor

**Important:** The `config.json` file is excluded from git (via `.gitignore`) to protect your sensitive information.

### Step 3: Set Permissions
Make the shell script executable:

```bash
chmod +x copy_for_youtube.sh
# or
chmod 755 copy_for_youtube.sh
```

### Step 4: Verify File Structure
Ensure `copy_for_youtube.py` and `copy_for_youtube.sh` are in the same directory (the shell script uses relative paths).

## Usage

### Manual Execution

#### Standard Run
Scans for new files and performs copy operations:
```bash
bash /path/to/copy_for_youtube.sh
```

#### Report Run with Notification
Executes workflow and sends summary to Discord:
```bash
bash /path/to/copy_for_youtube.sh notify
```

### Automated Scheduling

#### Using Cron (Linux/Unix)
Add to your crontab (`crontab -e`):

```bash
# Run every 30 minutes
*/30 * * * * bash /path/to/copy_for_youtube.sh

# Send daily report at 2 AM
0 2 * * * bash /path/to/copy_for_youtube.sh notify
```

#### Using Synology Task Scheduler
1. Open Control Panel → Task Scheduler
2. Create → Scheduled Task → User-defined script
3. Schedule: Set your preferred frequency
4. Task Settings → User-defined script:
   ```bash
   bash /path/to/copy_for_youtube.sh
   ```

## Status Lifecycle

The script manages three states for each file:

| Status | Description | Trigger |
|--------|-------------|---------|
| **0 (New)** | File discovered in source directory, meets size criteria | Automatic scan |
| **1 (Copied)** | File successfully copied to target directory | After copy operation |
| **2 (Completed)** | File found in completed directory, processing finished | File moved to completed dir |

### Workflow Diagram
```
[Source Dir] → Status 0 (New) 
    ↓ (Auto Copy)
[Upload Dir] → Status 1 (Copied)
    ↓ (Manual/External Process)
[Completed Dir] → Status 2 (Completed)
```

## Configuration Reference

### Directory Structure Example
```
/volume1/video/
├── raw/              # source_dir - New recordings
├── upload/           # upload_dir - Ready for processing
├── completed/        # completed_dir - Finished files
└── workflow.db       # db_path - SQLite database
```

### Database Schema
```sql
CREATE TABLE files (
    filepath TEXT PRIMARY KEY,
    filename TEXT,
    status INTEGER DEFAULT 0,
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    history TEXT DEFAULT ''
);
```

### Discord Notification Format
When using `notify` parameter, the script sends a Discord embed with:
- New files discovered (24h)
- Files copied to upload directory (24h)
- Files marked as completed (24h)
- Total database statistics by status

## Troubleshooting

### Common Issues

**Issue:** Script doesn't find new files
- Verify `source_dir` path is correct
- Check file size meets `min_size_mb` threshold
- Confirm file extensions match `extensions` list

**Issue:** Copy operation fails
- Check write permissions on `upload_dir`
- Verify sufficient disk space
- Review error messages in console output

**Issue:** Discord notifications not working
- Verify `webhook_url` is valid
- Test webhook URL manually
- Check network connectivity

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) file for details.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on the contribution process.