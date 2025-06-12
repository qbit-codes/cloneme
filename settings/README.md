# CloneMe Settings Configuration

> **⚙️ Hot-reloadable settings system for dynamic AI behavior configuration**

## Overview

CloneMe uses a sophisticated settings management system that supports:
- **🔥 Hot-reload**: Changes take effect immediately without restart
- **🔒 Thread-safe**: Concurrent access protection
- **✅ Validation**: Schema validation with error handling
- **📁 File watching**: Automatic detection of settings file changes
- **🛡️ Fallbacks**: Graceful degradation with default values

## File Structure

```
settings/
├── settings.json          # Main configuration file
└── README.md              # This documentation
```

## Quick Start

1. **Create settings file** (auto-created on first run):
   ```bash
   # Settings file is automatically created at settings/settings.json
   ```

2. **Edit settings** while CloneMe is running:
   ```bash
   # Changes are automatically detected and applied
   nano settings/settings.json
   ```

3. **Verify changes** in logs:
   ```
   ✅ Settings loaded successfully
   🔄 Settings reloaded due to file change
   ```

## Settings Schema

### AI Behavior Settings

#### Decision Making
Controls AI decision-making processes and caching:

```json
{
  "ai_behavior": {
    "decision_making": {
      "cache_ttl_seconds": {
        "security": 3600,        // Security analysis cache (1 hour)
        "classification": 1800,  // Message classification cache (30 min)
        "information_value": 600 // Information value cache (10 min)
      }
    }
  }
}
```

**Effects:**
- Higher values = Better performance, less AI calls
- Lower values = More accurate, up-to-date decisions
- `0` = Disable caching (not recommended)

#### Typing Simulation
Realistic typing indicators for human-like behavior:

```json
{
  "ai_behavior": {
    "typing_simulation": {
      "enabled": true,                    // Enable/disable typing simulation
      "base_speed_range": [3.5, 5.0],   // Characters per second range
      "thinking_time_range": [0.5, 2.0], // Pause before typing (seconds)
      "reading_pause_range": [0.3, 1.0], // Reading time per message
      "min_delay_seconds": 0.5,          // Minimum delay before response
      "max_delay_seconds": 15.0,         // Maximum delay before response
      "thinking_threshold_chars": 100,    // Message length to trigger thinking
      "reading_threshold_chars": 50       // Message length to trigger reading pause
    }
  }
}
```

**Effects:**
- `enabled: false` = Instant responses (robotic)
- Higher speeds = Faster typing (less human-like)
- Longer thinking times = More realistic pauses

#### Context Engine
Controls conversation context and memory integration:

```json
{
  "ai_behavior": {
    "context_engine": {
      "max_context_messages": 10,         // Number of previous messages to include
      "prioritize_recent_messages": true, // Weight recent messages higher
      "context_position_priority": "high", // Context importance level
      "include_message_timing": true,     // Include timestamps in context
      "include_sender_info": true,        // Include sender information
      "context_preview_length": 150,     // Preview length for context messages
      "show_full_recent_messages": 3      // Number of recent messages shown in full
    }
  }
}
```

**Effects:**
- Higher `max_context_messages` = Better conversation awareness, more AI tokens used
- `include_message_timing: false` = Faster processing, less temporal awareness
- Lower `context_preview_length` = Less context detail, faster processing

### Platform Settings

#### Participation Control
Prevents over-chatting and controls AI engagement:

```json
{
  "participation_control": {
    "enabled": true,                    // Enable participation limiting
    "threshold_percentage": 30,         // Max % of messages AI can send
    "time_window_minutes": 10,          // Time window for percentage calculation
    "group_chat_threshold": 30,         // Group chat participation limit (%)
    "direct_message_threshold": 50,     // DM participation limit (%)
    "description": "Controls AI participation rate limiting to prevent over-chatting"
  }
}
```

**Effects:**
- `enabled: false` = AI responds to everything (may seem spammy)
- Higher thresholds = More AI participation
- Shorter time windows = More responsive to recent activity

#### Flagged Messages
Controls handling of inappropriate content:

```json
{
  "platform_settings": {
    "flagged_messages": {
      "max_flagged_messages_per_channel": 5  // Max flagged messages to track per channel
    }
  }
}
```

### Debug Settings

#### Logging
Controls detailed logging for troubleshooting:

```json
{
  "debug": {
    "logging": {
      "detailed_ai_decisions": false,    // Log detailed AI decision processes
      "log_api_calls": false,           // Log all AI provider API calls
      "log_context_formatting": true    // Log context building process
    },
    "development": {
      "debug_mode": false,              // Enable development debugging
      "verbose_errors": false           // Show detailed error information
    }
  }
}
```

**Effects:**
- `detailed_ai_decisions: true` = Verbose decision logs (helpful for debugging)
- `log_api_calls: true` = Shows all AI API requests (may expose sensitive data)
- `debug_mode: true` = Additional development logging

### Notifications

#### Startup & Runtime
Controls system notifications:

```json
{
  "notifications": {
    "startup": {
      "enabled": true,              // Show startup notifications
      "show_config_status": true    // Show configuration status on startup
    },
    "runtime": {
      "config_reload_notifications": true,  // Notify when settings reload
      "error_notifications": true           // Show error notifications
    }
  }
}
```

## Advanced Configuration

### Custom Settings
You can add custom settings sections for your own use:

```json
{
  "my_custom_settings": {
    "feature_flags": {
      "experimental_mode": false,
      "beta_features": true
    },
    "custom_thresholds": {
      "response_confidence": 0.8,
      "memory_importance": 0.6
    }
  }
}
```

Access custom settings in code:
```python
# Get custom setting with dot notation
value = settings_manager.get('my_custom_settings.feature_flags.experimental_mode', False)
```

### Environment-Specific Settings
Create different settings for different environments:

```json
{
  "_metadata": {
    "environment": "production",  // or "development", "testing"
    "version": "1.0.0"
  }
}
```

## API Reference

### SettingsManager Methods

```python
# Get a setting value
value = settings_manager.get('ai_behavior.typing_simulation.enabled', True)

# Set a setting value
settings_manager.set('debug.logging.detailed_ai_decisions', True)

# Check if a feature is enabled
if settings_manager.is_enabled('participation_control.enabled'):
    # Feature is enabled

# Register change callback
def on_settings_change(new_settings):
    print("Settings changed!")
settings_manager.add_change_callback(on_settings_change)

# Manual reload
settings_manager.reload()
```

## Troubleshooting

### Common Issues

1. **Settings not reloading**
   ```bash
   # Check file permissions
   ls -la settings/settings.json
   
   # Check logs for file watching errors
   tail -f logs/*/platform_manager.log
   ```

2. **Invalid JSON format**
   ```bash
   # Validate JSON syntax
   python -m json.tool settings/settings.json
   ```

3. **Validation errors**
   ```bash
   # Check logs for validation details
   grep "validation" logs/*/settings_manager.log
   ```

### Performance Tips

- **Cache TTL**: Start with default values, adjust based on usage
- **Context Messages**: Reduce if experiencing slow responses
- **Debug Logging**: Disable in production for better performance

### Backup & Recovery

Settings are automatically backed up when modified. To restore:

```bash
# Settings manager creates backups automatically
# Check for backup files in settings/ directory
ls settings/*.backup
```

---

**📚 Related Documentation:**
- [Profile Configuration](../profiles/README.md)
- [Memory System](../memories/README.md)
- [Message Flow](../docs/MESSAGE_FLOW.md)
- [Main Documentation](../README.md)
