import datetime
import random
import module_a

APP_CONFIG_B = {
    "module_name": "ModuleB",
    "log_level": "INFO",
    "max_sessions_per_user": 3
}

def get_user_sessions(user_id):
    num_sessions = random.randint(1, APP_CONFIG_B['max_sessions_per_user'])
    sessions = []
    for i in range(num_sessions):
        session_id = f"SESS-{user_id}-{random.randint(100, 999)}"
        session_duration = random.randint(30, 300)
        sessions.append({
            "session_id": session_id,
            "duration_sec": session_duration,
            "timestamp": datetime.datetime.now().isoformat()
        })
    print(f"[ModuleB] Fetched {len(sessions)} sessions for user {user_id}.")
    return sessions

def log_activity_from_module_a(activity_message):
    log_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_log = f"[{log_timestamp}] [LOG] [ModuleB] Received activity from ModuleA: '{activity_message}'"
    print(formatted_log)
    
    
    
    
    

def initialize_module_b():
    print(f"\n[{APP_CONFIG_B['module_name']}] Initializing (Log Level: {APP_CONFIG_B['log_level']})...")
    
    print(f"[{APP_CONFIG_B['module_name']}] Initialization complete.")

if __name__ == "__main__":
    initialize_module_b()
