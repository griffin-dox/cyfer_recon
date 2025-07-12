# Enhanced Preset System for Cyfer Recon

## Overview

The Cyfer Recon tool now supports two types of presets to give you maximum flexibility in your reconnaissance workflows:

1. **Task-based Presets** (Original) - Collections of predefined task categories
2. **Command-based Presets** (New) - Custom collections of direct commands with placeholders

## Task-based Presets

Task-based presets reference predefined task categories from `tasks.json`. These are ideal for:
- Standardized workflows
- Maintaining consistency across different reconnaissance sessions
- Leveraging the full power of predefined task categories

### Built-in Task-based Presets:
- **Quick Recon**: Fast, minimal recon for quick results
- **Full Recon**: Comprehensive recon using all available modules
- **API Recon**: Recon focused on APIs, endpoints, secrets, and code leaks

### Creating Custom Task-based Presets:
```bash
cyfer-recon  # Start interactive mode
# Select "Create Task Preset"
# Choose tasks from the list
# Name your preset and add description
```

## Command-based Presets

Command-based presets contain direct commands with placeholders. These are perfect for:
- Highly customized workflows
- Specific use cases not covered by standard tasks
- Quick prototyping of new reconnaissance techniques
- Combining tools in unique ways

### Built-in Command-based Presets:
- **My Quick Scan**: Fast custom scan with specific tools
- **My Subdomain Hunt**: Custom subdomain enumeration workflow
- **My API Security Test**: Comprehensive API security testing
- **My Web App Deep Scan**: Thorough web application testing

### Command Placeholders:
- `{target}` - Target domain/host
- `{output}` - Output directory
- `{wordlist}` - Wordlist path for the tool

### Example Commands:
```bash
# Port scanning with custom output
nmap -sS -sV -T4 -p- {target} -oN {output}/custom_nmap_{target}.txt

# HTTP probing with custom headers
httpx -u https://{target} -sc -title -tech-detect -o {output}/custom_httpx_{target}.txt

# Vulnerability scanning with specific tags
nuclei -u https://{target} -tags cve,exposure,xss -o {output}/custom_nuclei_{target}.txt
```

## Commands

### List All Presets:
```bash
cyfer-recon list-presets
```

### Edit Task-based Presets:
```bash
cyfer-recon preset-edit
```

### Edit Command-based Presets:
```bash
cyfer-recon custom-preset-edit
```

### Run a Specific Preset:
```bash
cyfer-recon --preset "My Quick Scan"
```

## Configuration Files

### Task-based Presets:
- **File**: `config/presets.json`
- **Structure**: 
```json
{
  "Preset Name": {
    "tasks": ["Task 1", "Task 2", ...],
    "description": "Preset description"
  }
}
```

### Command-based Presets:
- **File**: `config/custom_presets.json`
- **Structure**:
```json
{
  "Custom Preset Examples": {
    "description": "Example custom presets",
    "presets": {
      "Preset Name": {
        "description": "Preset description",
        "commands": ["command1", "command2", ...]
      }
    }
  }
}
```

## Usage Examples

### Interactive Mode:
```bash
cyfer-recon
# You'll see options like:
# [Task] Quick Recon - Fast, minimal recon for quick results
# [Task] Full Recon - Comprehensive recon using all available modules
# [Command] My Quick Scan - Fast custom scan with specific tools
# [Command] My Subdomain Hunt - Custom subdomain enumeration workflow
# Create Task Preset
# Create Command Preset
# Custom (One-off)
```

### Creating a Custom Command Preset:
```bash
cyfer-recon
# Select "Create Command Preset"
# Enter commands one by one:
# 1. nmap -sS -sV {target} -oN {output}/my_nmap_{target}.txt
# 2. httpx -u https://{target} -sc -title -o {output}/my_httpx_{target}.txt
# 3. nuclei -u https://{target} -tags cve -o {output}/my_nuclei_{target}.txt
# (Press Enter with empty line to finish)
# Name your preset: "My Custom Scan"
# Description: "Custom scan with nmap, httpx, and nuclei"
```

### Editing Existing Presets:
```bash
# Edit command-based presets
cyfer-recon custom-preset-edit

# Edit task-based presets  
cyfer-recon preset-edit
```

## Benefits

### Task-based Presets:
- ✅ Leverage predefined, tested task categories
- ✅ Easy to maintain and update
- ✅ Consistent across different environments
- ✅ Built-in error handling and validation

### Command-based Presets:
- ✅ Complete flexibility in command construction
- ✅ Custom output file naming
- ✅ Unique tool combinations
- ✅ Rapid prototyping of new techniques
- ✅ Tool-specific parameter customization

## Best Practices

1. **Use Task-based Presets** for standard reconnaissance workflows
2. **Use Command-based Presets** for specialized or custom workflows
3. **Name presets descriptively** to make them easy to identify
4. **Add descriptions** to explain the purpose of each preset
5. **Test presets** in dry-run mode before running on targets
6. **Use placeholders** consistently in command-based presets
7. **Keep commands simple** and focused on single tasks when possible

## Migration from Old System

The new system is fully backward compatible. Your existing presets will continue to work as task-based presets. You can now enhance your workflows by:

1. Creating command-based presets for specialized use cases
2. Customizing individual commands for specific tools
3. Combining both types of presets in your reconnaissance workflow

This enhanced preset system gives you the best of both worlds - the reliability of predefined tasks and the flexibility of custom commands!
