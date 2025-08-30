from decouple import config

print("DB_NAME:", config('DB_NAME'))
print("DB_USER:", config('DB_USER'))
print("DB_PASSWORD:", config('DB_PASSWORD'))
print("DB_HOST:", config('DB_HOST', default='localhost'))
print("DB_PORT:", config('DB_PORT', default='3306'))# --- IGNORE ---
# Django settings for riego_indoor project.