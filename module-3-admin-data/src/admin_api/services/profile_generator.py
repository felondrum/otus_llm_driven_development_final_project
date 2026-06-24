# ===========================================
# Profile Generator Service
# ===========================================

import logging
from typing import Dict, List, Optional
import random

logger = logging.getLogger(__name__)


class ProfileGenerator:
    """Generate test/demo user profiles"""
    
    # Sample data for generation
    first_names = [
        "Ivan", "Petr", "Sergei", "Alexei", "Dmitry", "Evgeny", "Andrey", "Mikhail",
        "Maria", "Anna", "Elena", "Olga", "Svetlana", "Tatiana", "Natalia", "Ekaterina"
    ]
    
    last_names = [
        "Ivanov", "Petrov", "Sergeev", "Alexeev", "Dmitriev", "Evgeniev", "Andreev", "Mikhailov",
        "Smirnov", "Popov", "Vasiliev", "Kuznetsov", "Sokolov", "Melnikov", "Novikov", "Morozov"
    ]
    
    roles = ["user", "moderator", "admin", "guest"]
    
    domains = ["example.com", "company.com", "mail.ru", "gmail.com"]
    
    departments = [
        "Engineering", "Sales", "Marketing", "HR", "Finance", "Support",
        "Legal", "Operations", "Product", "Design"
    ]
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
    
    def generate_profile(self, user_id: Optional[str] = None) -> Dict:
        """Generate a single user profile"""
        if user_id is None:
            user_id = f"user_{random.randint(1000, 9999)}"
        
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        email_domain = random.choice(self.domains)
        
        profile = {
            "user_id": user_id,
            "full_name": f"{last_name} {first_name}",
            "email": f"{first_name.lower()}.{last_name.lower()}@{email_domain}",
            "role": random.choice(self.roles),
            "department": random.choice(self.departments),
            "is_active": random.random() > 0.1,  # 90% active
            "metadata": {
                "created_at": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "last_login": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed={user_id}",
                "bio": f"{first_name} works in {random.choice(self.departments)} department."
            }
        }
        
        return profile
    
    def generate_profiles(self, count: int = 10, prefix: str = "user") -> List[Dict]:
        """Generate multiple user profiles"""
        profiles = []
        
        for i in range(count):
            user_id = f"{prefix}_{i+1:04d}"
            profile = self.generate_profile(user_id)
            profiles.append(profile)
        
        return profiles
    
    def generate_demo_profiles(self) -> List[Dict]:
        """Generate demo profiles for testing"""
        profiles = []
        
        # Admin
        profiles.append({
            "user_id": "admin_001",
            "full_name": "Administrator User",
            "email": "admin@demo.com",
            "role": "admin",
            "department": "Operations",
            "is_active": True,
            "metadata": {
                "created_at": "2024-01-01",
                "last_login": "2024-06-15",
                "avatar_url": "https://api.dicebear.com/7.x/avataaars/svg?seed=admin"
            }
        })
        
        # Moderators
        for i in range(1, 4):
            profiles.append({
                "user_id": f"mod_{i:03d}",
                "full_name": f"Moderator User {i}",
                "email": f"mod{i}@demo.com",
                "role": "moderator",
                "department": random.choice(["Support", "Operations", "Legal"]),
                "is_active": True,
                "metadata": {
                    "created_at": f"2024-01-{i+1:02d}",
                    "last_login": f"2024-06-{i+10:02d}",
                    "avatar_url": f"https://api.dicebear.com/7.x/avataaars/svg?seed=mod{i}"
                }
            })
        
        # Regular users
        profiles.extend(self.generate_profiles(20, prefix="user"))
        
        return profiles
    
    def generate_bulk_data(self, count: int = 100, output_file: Optional[str] = None) -> List[Dict]:
        """Generate bulk profile data and optionally save to file"""
        profiles = self.generate_profiles(count)
        
        if output_file:
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({"profiles": profiles}, f, indent=2, ensure_ascii=False)
            logger.info(f"Generated {count} profiles saved to {output_file}")
        
        return profiles
