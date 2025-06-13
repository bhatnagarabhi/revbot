import datetime
import random
import module_b

APP_CONFIG_A = {
    "module_name": "ModuleA",
    "version": "1.0",
    "max_users_to_process": 5
}

def create_user_profile(username, email):
    profile_id = f"USER-{random.randint(1000, 9999)}"
    creation_timestamp = datetime.datetime.now().isoformat()
    print(f"[ModuleA] Creating profile for {username} (ID: {profile_id})...")
    return {
        "profile_id": profile_id,
        "username": username,
        "email": email,
        "created_at": creation_timestamp
    }

def aggregate_data_from_users(user_list):
    print(f"[ModuleA] Aggregating data for {len(user_list)} users.")
    total_data_points = 0
    for user in user_list:
        user_sessions = module_b.get_user_sessions(user["profile_id"])
        total_data_points += len(user_sessions) * random.randint(1, 5)
        print(f"[ModuleA]   Processed sessions for {user['username']}. Total data points updated.")

    print(f"[ModuleA] Aggregation complete. Total simulated data points: {total_data_points}.")
    return total_data_points

def initialize_module_a():
    print(f"\n[{APP_CONFIG_A['module_name']}] Initializing (Version: {APP_CONFIG_A['version']})...")
    
    module_b.log_activity_from_module_a("ModuleA started its initialization process.")

    dummy_users = []
    for i in range(APP_CONFIG_A['max_users_to_process']):
        user = create_user_profile(f"user_{i+1}", f"user{i+1}@example.com")
        dummy_users.append(user)

    if dummy_users:
        aggregate_data_from_users(dummy_users)
    
    print(f"[{APP_CONFIG_A['module_name']}] Initialization complete.")

if __name__ == "__main__":
    initialize_module_a()
