# 🗄️ Internal Tools Database - Quick Setup

Ready-to-use database environment for API development tests.

## 🚀 Quick Start (Choose Your Stack)

### Option 1: MySQL + phpMyAdmin 
```bash
# Method 1: Script (recommended)
chmod +x start-mysql.sh && ./start-mysql.sh

# Method 2: Direct command
docker-compose --profile mysql up -d
```

**Access in 30 seconds:**
- 🗄️ **MySQL:** `localhost:3306`
- 🌐 **phpMyAdmin:** http://localhost:8080
- 👤 **Credentials:** `dev / dev123`
- 📊 **Database:** `internal_tools`

### Option 2: PostgreSQL + pgAdmin 
```bash
# Method 1: Script (recommended)
chmod +x start-postgres.sh && ./start-postgres.sh

# Method 2: Direct command  
docker-compose --profile postgres up -d
```

**Access in 30 seconds:**
- 🗄️ **PostgreSQL:** `localhost:5432` 
- 🌐 **pgAdmin:** http://localhost:8081
- 👤 **Credentials:** `dev / dev123`
- 📊 **Database:** `internal_tools`

### Option 3: Both Databases (Testing)
```bash
docker-compose --profile all up -d
```



## 🛠️ Quick Commands

```bash
# Test connections
./test-connections.sh

# Stop everything
docker-compose --profile all down

# Reset all data (⚠️ destructive)
./reset-all.sh

# View logs
docker-compose logs -f mysql     # or postgres
```

## 📊 Connection Strings

```bash
# MySQL
mysql://dev:dev123@localhost:3306/internal_tools
"mysql:host=localhost;port=3306;dbname=internal_tools"

# PostgreSQL  
postgresql://dev:dev123@localhost:5432/internal_tools
"pgsql:host=localhost;port=5432;dbname=internal_tools"
```

---

## **⚡ COMMANDES  FINALES**

### **🐬 Pour MySQL **
```bash
docker-compose --profile mysql up -d
# ✅ MySQL + phpMyAdmin prêts !
# 🌐 Interface: http://localhost:8080
```

### **🐘 Pour PostgreSQL **  
```bash
docker-compose --profile postgres up -d
# ✅ PostgreSQL + pgAdmin prêts !
# 🌐 Interface: http://localhost:8081
```

### **🎯 Pour Tests Comparatifs**
```bash
docker-compose --profile all up -d  
# ✅ Les deux bases + interfaces prêtes !
```
