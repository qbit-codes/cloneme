from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .config.profile_manager import ProfileManager
    from .config.profile import Profile

class Config:
    """
    Legacy configuration class - now acts as a bridge to the new ProfileManager system.
    """
    
    _profile_manager: Optional[ProfileManager] = None
    _current_profile: Optional[Profile] = None
    
    @classmethod
    def get_profile_manager(cls, profiles_directory: Optional[str] = None) -> ProfileManager:
        """Get or create a ProfileManager instance."""
        if cls._profile_manager is None:
            if profiles_directory is None:
                profiles_directory = Path(__file__).parent.parent
            cls._profile_manager = ProfileManager(profiles_directory)
        return cls._profile_manager
    
    @classmethod
    def load_profile(cls, profile_name: str = "default") -> Optional[Profile]:
        """Load a profile by name."""
        manager = cls.get_profile_manager()
        cls._current_profile = manager.get_profile(profile_name)
        return cls._current_profile
    
    @classmethod
    def get_current_profile(cls) -> Optional[Profile]:
        """Get the currently loaded profile."""
        return cls._current_profile