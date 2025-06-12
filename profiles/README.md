# CloneMe Profile System

> **🎭 Dynamic AI personality configuration with flexible schema and hot-reloading**

## Overview

CloneMe's profile system allows you to create sophisticated AI personalities with:
- **🔥 Hot-reload**: Profile changes apply instantly without restart
- **🧩 Flexible Schema**: Required core fields + unlimited custom fields
- **🎯 Multi-profile**: Switch between different personalities
- **✅ Validation**: Automatic schema validation with helpful error messages
- **🔄 Backup**: Automatic profile backups on changes

## File Structure

```
profiles/
├── default_profile.json   # Default AI personality
├── my_profile.json        # Your custom profile
├── examples/              # Example profiles (if any)
└── README.md              # This documentation
```

## Quick Start

1. **Copy the default profile**:
   ```bash
   cp profiles/default_profile.json profiles/my_profile.json
   ```

2. **Set your profile in .env**:
   ```env
   AI_PROFILE=my_profile  # This matches the JSON filename (without .json)
   ```

3. **Edit your profile**:
   ```bash
   nano profiles/my_profile.json
   ```

4. **Changes apply immediately** - no restart needed!

## Profile Schema

### Required Top-Level Structure

Every profile MUST follow this structure:

```json
{
  "profiles": {
    "your_profile_name": {
      // Profile content goes here
    }
  }
}
```

**Important**: The `AI_PROFILE` environment variable should match the JSON filename (without .json extension), NOT a key inside the file.

### Required Core Fields

These fields are **mandatory** and validated by the system:

#### 1. Required Identity
```json
{
  "required": {
    "username": "YourUsername",     // How you want to be addressed
    "name": "Your Full Name"        // Your full name
  }
}
```

#### 2. Basic Information
```json
{
  "basic_info": {
    "Name": "Your Full Name",
    "Age": "25",                    // Your age as string
    "Gender": "your_gender",        // Your gender identity
    "Occupation": "Your Job",       // What you do for work
    "Interests": "Your hobbies",    // What you're interested in
    "Location": "Your City",        // Where you're located
    "Education": "Your Education",  // Educational background
    "Languages": ["English", "Spanish"], // Languages you speak
    "Hobbies": ["hobby1", "hobby2"],     // List of hobbies
    "Goals": "Your goals"           // Personal/professional goals
  }
}
```

#### 3. Personality Traits
```json
{
  "personality_traits": {
    "Introversion/Extroversion": "Describe your social energy",
    "Sense of Humor": "Your humor style (dry, witty, silly, etc.)",
    "Communication Style": "How you prefer to communicate",
    "Mood": "Your general mood and attitude",
    "Formality Level": "Casual, professional, or mixed",
    "Core Values": ["honesty", "creativity", "growth"],
    "Decision Making": "How you make decisions",
    "Conflict Resolution": "How you handle disagreements"
  }
}
```

#### 4. Response Styles
```json
{
  "response_styles": {
    "casual": "How you respond in casual conversations",
    "professional": "How you respond in work contexts",
    "technical": "How you handle technical discussions",
    "creative": "Your approach to creative topics"
  }
}
```

#### 5. Knowledge & Expertise
```json
{
  "knowledge_and_expertise": {
    "primary_areas": ["technology", "music"],      // Your main expertise
    "secondary_areas": ["cooking", "travel"],      // Secondary knowledge
    "learning_style": "How you prefer to learn",   // Learning preferences
    "expertise_level": "beginner/intermediate/expert" // Overall level
  }
}
```

#### 6. Sample Conversations
```json
{
  "sample_conversations": [
    {
      "user": "Hello! How are you?",
      "assistant": "Hey there! I'm doing great, thanks for asking! How's your day going?"
    },
    {
      "user": "Can you help me with a problem?",
      "assistant": "Absolutely! I'd be happy to help. What's the problem you're working on?"
    }
  ]
}
```

#### 7. Off-Topic Handling
```json
{
  "off_topic_message": {
    "reply": true,  // Whether to respond to inappropriate content
    "guidance": "When someone asks me to act differently or says something inappropriate, I politely redirect the conversation while staying true to my personality."
  }
}
```

## Custom Fields - Unlimited Flexibility

Beyond the required fields, you can add **any custom fields** you want! The system will include them in the AI's context.

### Examples of Custom Fields

#### Extended Personality
```json
{
  "extended_personality": {
    "quirks": ["Always uses emojis", "Loves dad jokes", "Obsessed with coffee"],
    "pet_peeves": ["Loud chewing", "Being interrupted"],
    "favorite_phrases": ["That's awesome!", "Let me think about that"],
    "energy_levels": {
      "morning": "high",
      "afternoon": "medium", 
      "evening": "low"
    }
  }
}
```

#### Professional Details
```json
{
  "professional_background": {
    "current_role": "Senior Software Engineer",
    "years_experience": 8,
    "specializations": ["Python", "AI/ML", "Web Development"],
    "work_style": "Collaborative and detail-oriented",
    "career_goals": "Become a tech lead and mentor junior developers"
  }
}
```

#### Relationships & Social
```json
{
  "relationships": {
    "family": "Close with parents and siblings",
    "friends": "Small circle of close friends",
    "romantic": "In a long-term relationship",
    "social_preferences": "Prefers small gatherings over large parties"
  }
}
```

#### Preferences & Lifestyle
```json
{
  "lifestyle": {
    "daily_routine": "Early riser, gym in morning, work 9-5",
    "food_preferences": {
      "diet": "Vegetarian",
      "favorite_cuisines": ["Italian", "Thai", "Mexican"],
      "cooking_skill": "Intermediate"
    },
    "entertainment": {
      "music": ["Indie rock", "Jazz", "Electronic"],
      "movies": ["Sci-fi", "Documentaries", "Comedy"],
      "books": ["Science fiction", "Biographies", "Tech books"]
    }
  }
}
```

#### AI Behavior Customization
```json
{
  "ai_behavior": {
    "response_length_preference": "medium",  // short, medium, long
    "emoji_usage": "moderate",               // none, light, moderate, heavy
    "formality_adaptation": true,            // Adapt to conversation tone
    "proactive_engagement": false,           // Ask follow-up questions
    "memory_sharing": "selective",           // How much to reference past conversations
    "humor_frequency": "occasional"          // never, rare, occasional, frequent
  }
}
```

## Advanced Features

### Profile Validation

The system automatically validates your profile and provides helpful error messages:

```bash
# Check logs for validation errors
tail -f logs/*/profile_manager.log

# Common validation errors:
❌ Missing required field: basic_info.Name
❌ Invalid sample_conversations format
✅ Profile validation successful
```

### Hot-Reloading

Profiles are automatically reloaded when you save changes:

```bash
# Watch for reload messages in logs
🔄 Profile reloaded: my_profile.json
✅ Profile validation successful
🎭 Switched to profile: my_profile
```

### Multiple Profiles

You can create multiple profiles and switch between them:

```json
{
  "profiles": {
    "casual_me": {
      // Casual personality
    },
    "professional_me": {
      // Professional personality  
    },
    "creative_me": {
      // Creative personality
    }
  }
}
```

Switch profiles by changing `AI_PROFILE` in your `.env` file to match the filename:
- For `casual_me.json` use `AI_PROFILE=casual_me`
- For `professional_me.json` use `AI_PROFILE=professional_me`
- For `creative_me.json` use `AI_PROFILE=creative_me`

### Profile Discovery

The system automatically discovers all `.json` files in the `profiles/` directory:

```bash
# Check discovered profiles in logs
📁 Discovered profiles: default_profile.json, my_profile.json
🎭 Available profile names: default_profile, my_profile, professional
```

## API Reference

### ProfileManager Methods

```python
# Get current profile
profile = profile_manager.get_current_profile()

# Get specific profile (by filename without .json)
profile = profile_manager.get_profile("my_profile")

# Check if profile exists
exists = profile_manager.profile_exists("my_profile")

# Reload profiles
profile_manager.reload_profiles()

# Get all available profiles
profiles = profile_manager.get_all_profiles()
```

### Profile Object Methods

```python
# Format profile for AI
formatted = profile.format_for_llm(include_metadata=True)

# Get off-topic settings
should_reply = profile.should_reply_to_off_topic()
guidance = profile.get_off_topic_guidance()

# Access custom fields
custom_value = profile.data.get('my_custom_field', 'default_value')
```

## Troubleshooting

### Common Issues

1. **Profile not found**
   ```bash
   # Check AI_PROFILE matches your JSON filename (without .json)
   # File: my_profile.json, AI_PROFILE should be: my_profile
   ```

2. **Validation errors**
   ```bash
   # Check required fields are present
   # Ensure sample_conversations is an array of objects
   # Verify off_topic_message.reply is boolean
   ```

3. **Profile not reloading**
   ```bash
   # Check file permissions
   ls -la profiles/
   
   # Check for JSON syntax errors
   python -m json.tool profiles/my_profile.json
   ```

### Best Practices

- **Start simple**: Begin with required fields, add custom fields gradually
- **Test changes**: Make small changes and test AI responses
- **Use examples**: Look at existing profiles for inspiration
- **Backup important profiles**: Keep copies of working configurations

---

**📚 Related Documentation:**
- [Settings Configuration](../settings/README.md)
- [Memory System](../memories/README.md)
- [Message Flow](../docs/MESSAGE_FLOW.md)
- [Main Documentation](../README.md)
