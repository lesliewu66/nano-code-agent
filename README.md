# Multi-Agent Login System

A complete login system built with multiple AI agents working collaboratively.

## System Architecture

This system uses a multi-agent architecture where each agent has a specific responsibility:

### Agents Overview

1. **DatabaseAgent** 🤖
   - Role: Database Manager
   - Responsibility: User data storage and retrieval
   - Storage: SQLite database (`users.db`)
   - Table: `users` (id, username, password_hash, created_at)

2. **UserManagementAgent** 👤
   - Role: User Registration Manager
   - Responsibility: New user registration with validation
   - Features:
     - Username validation (3-20 chars, alphanumeric)
     - Password length requirement (min 6 chars)
     - Duplicate username prevention
     - Password hashing with bcrypt

3. **AuthenticationAgent** 🔐
   - Role: Authentication Manager
   - Responsibility: User login, logout, and session management
   - Features:
     - Credential verification
     - Secure session token generation
     - Active session tracking
     - Password validation with bcrypt

4. **Main Coordinator** 🎛️
   - Role: System Coordinator
   - Responsibility: Integration and user interface
   - Features:
     - Command-line interface
     - Coordination between all agents
     - Session management
     - User management

## Features

### User Management
- ✅ User registration with validation
- ✅ Password hashing (bcrypt)
- ✅ Username uniqueness check
- ✅ List all registered users

### Authentication
- ✅ User login with credential verification
- ✅ Secure session token generation (64-char hex)
- ✅ Session validation
- ✅ User logout with session invalidation
- ✅ Active session tracking

### Security Features
- ✅ Password hashing with salt (bcrypt)
- ✅ Secure session tokens
- ✅ Username format validation
- ✅ Password length enforcement

## Installation

1. Install required dependencies:
```bash
pip install bcrypt
```

2. Initialize the database:
```bash
sqlite3 users.db "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);"
```

## Usage

### Running the System

```bash
python login_system.py
```

### Menu Options

1. **Register new user**
   - Enter username (3-20 alphanumeric characters)
   - Enter password (min 6 characters)
   - System validates and creates user account

2. **Login**
   - Enter username and password
   - System verifies credentials
   - Returns session token upon success

3. **Logout**
   - Enter session token
   - Invalidates the session

4. **List all users**
   - Shows all registered users with creation dates

5. **Show active sessions**
   - Displays all currently active login sessions

6. **Verify session token**
   - Validates a session token
   - Returns associated username if valid

7. **Exit**
   - Shuts down the system
   - Clears all active sessions

## Testing

### Run Individual Tests

**Test Registration:**
```bash
python test_registration.py
```

**Test Login:**
```bash
python test_login.py
```

### Test Flow

1. **Registration Flow:**
   - Username format validation
   - Username availability check
   - Password hashing
   - User creation in database

2. **Login Flow:**
   - User lookup
   - Password verification
   - Session token generation
   - Session storage

3. **Session Management:**
   - Token verification
   - Session invalidation on logout
   - Active session tracking

## Example Session

```
🚀 Starting Multi-Agent Login System...
System initialized with agents:
  - DatabaseAgent: Managing data storage
  - UserManagementAgent: Handling registrations
  - AuthenticationAgent: Managing authentication

==================================================
      MULTI-AGENT LOGIN SYSTEM
==================================================
1. Register new user
2. Login
3. Logout
4. List all users
5. Show active sessions
6. Verify session token
7. Exit
==================================================

Enter your choice (1-7): 1

=== USER REGISTRATION ===
Enter username (3-20 chars, alphanumeric): alice
Enter password (min 6 chars): mypassword

✅ Registration successful! Welcome, alice!

(Continue with login...)
```

## Technical Details

### Database Schema
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Password Hashing
- Algorithm: bcrypt
- Salt: Auto-generated
- Work factor: Default (12)

### Session Tokens
- Type: Cryptographically random
- Format: 64-character hexadecimal
- Storage: In-memory dictionary
- No expiration (for demo purposes)

## Security Notes

⚠️ **Important:** This is a demonstration system. For production use:
- Add HTTPS/TLS
- Implement session expiration
- Add rate limiting
- Use environment variables for secrets
- Add email verification
- Implement password reset functionality
- Add audit logging

## Cleanup

To reset the system:
```bash
# Stop the login_system.py if running
# Remove database
rm users.db
# Remove sessions (they're in-memory, so restart clears them)
```

## Files Structure

```
.
├── login_system.py          # Main coordinator with CLI
├── test_registration.py     # Registration test script
├── test_login.py           # Login test script
├── README.md               # This documentation
└── users.db                # SQLite database (created on first run)
```

## Agent Communication Flow

### Registration Flow:
```
User → Main Coordinator → UserManagementAgent 
                            ↓
                     DatabaseAgent (check exists)
                            ↓
                     DatabaseAgent (save user)
                            ↓
                    Success response
```

### Login Flow:
```
User → Main Coordinator → AuthenticationAgent
                            ↓
                     DatabaseAgent (get user)
                            ↓
                     AuthenticationAgent (verify password)
                            ↓
                     Generate session token
                            ↓
                    Return token
```

## Future Enhancements

- [ ] Add role-based access control (RBAC)
- [ ] Email verification system
- [ ] Password reset functionality
- [ ] Session expiration and refresh tokens
- [ ] API endpoints for web/mobile access
- [ ] Multi-factor authentication (MFA)
- [ ] Audit logging
- [ ] User profile management

## License

This is a demonstration system for educational purposes.
