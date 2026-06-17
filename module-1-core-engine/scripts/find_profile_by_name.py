#!/usr/bin/env python3
"""
Скрипт для поиска профиля по частичному совпадению имени.
Используется для отладки и поиска правильного user_id по имени пользователя.

Запуск в Docker контейнере:
    docker exec -it chameleon-orchestrator python /app/scripts/find_profile_by_name.py Иван

Запуск локально (требует poetry install):
    cd module-1-core-engine
    poetry run python scripts/find_profile_by_name.py Иван
"""

import sys
import os

# Добавляем src в path (для контейнера и локального запуска)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(base_dir, 'src')
if os.path.exists(src_dir):
    sys.path.insert(0, src_dir)

from retriever.qdrant_client import get_qdrant_client


def find_profile_by_name_fragment(name_fragment: str):
    """Поиск профиля по частичному совпадению имени."""
    qdrant = get_qdrant_client()
    
    # Получаем все профили
    result = qdrant.client.scroll(
        collection_name='user_profiles',
        limit=100,
        with_payload=True,
        with_vectors=False
    )
    
    profiles, _ = result
    
    # Ищем профили, где full_name содержит name_fragment
    matches = []
    for profile in profiles:
        full_name = profile.payload.get('full_name', '')
        user_id = profile.payload.get('user_id', '')
        
        if name_fragment.lower() in full_name.lower():
            matches.append({
                'user_id': user_id,
                'full_name': full_name,
                'role': profile.payload.get('role', ''),
                'department': profile.payload.get('department', '')
            })
    
    return matches


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Использование: python scripts/find_profile_by_name.py <часть_имени>")
        print("Пример: python scripts/find_profile_by_name.py Иван")
        print("Пример: python scripts/find_profile_by_name.py alex")
        sys.exit(1)
    
    name_fragment = sys.argv[1]
    print(f"Поиск профилей, содержащих '{name_fragment}'...")
    print("=" * 60)
    
    matches = find_profile_by_name_fragment(name_fragment)
    
    if matches:
        print(f"Найдено {len(matches)} профилей:\n")
        for match in matches:
            print(f"  user_id:    {match['user_id']}")
            print(f"  full_name:  {match['full_name']}")
            print(f"  role:       {match['role']}")
            print(f"  department: {match['department']}")
            print()
    else:
        print(f"Профили с '{name_fragment}' не найдены.")
        print("\nДоступные профили:")
        print("-" * 60)
        
        result = qdrant.client.scroll(
            collection_name='user_profiles',
            limit=100,
            with_payload=True,
            with_vectors=False
        )
        
        profiles, _ = result
        for profile in profiles:
            print(f"  {profile.payload.get('user_id')} - {profile.payload.get('full_name')}")
