# 🚀 Interactive Menu System

## Quick Start

```bash
# Launch the interactive menu
./menu

# Or run directly
./manage-menu.sh
```

## 📋 Menu Options

### **1️⃣ Update Specific App**
- Shows list of available apps
- Prompts for app name
- Updates that specific app
- Shows progress and results

### **2️⃣ Update All Apps** 
- Updates all configured apps
- Shows progress for each app
- Reports success/failure for each

### **3️⃣ Check GitHub Monitor Status**
- Shows systemd service status
- Displays if monitor is running
- Shows recent service activity

### **4️⃣ View Recent Monitor Logs**
- Live tail of monitor log file
- Shows real-time monitoring activity
- Press Ctrl+C to exit log view

### **5️⃣ View Container Logs**
- Choose specific app or 'all'
- Live tail of container logs
- Useful for debugging apps

### **6️⃣ Check Container Status**
- Shows docker-compose status
- Lists all containers and their state
- Shows ports and health status

### **7️⃣ Manual Monitor Run (Once)**
- Triggers immediate monitor check
- Bypasses 5-minute automatic schedule
- Shows immediate results

### **8️⃣ Show Available Apps**
- Lists all configured apps
- Reads from monitor configuration
- Shows what apps can be updated

### **9️⃣ Exit**
- Cleanly exits the menu system

## 🎨 Features

- **🌈 Colorized Output**: Easy to read status messages
- **📱 User-Friendly**: Clear prompts and instructions  
- **🔄 Persistent Menu**: Returns to menu after each operation
- **❌ Error Handling**: Validates input and shows helpful errors
- **🎯 Context Aware**: Shows relevant apps and options

## 🚀 Usage Examples

### **Quick Update:**
```bash
./menu
# Select: 1 (Update Specific App)
# Enter: n2s-tmmi-tracker
```

### **Check Everything:**
```bash
./menu  
# Select: 6 (Check Container Status)
# Then: 3 (Check Monitor Status)
```

### **Troubleshooting:**
```bash
./menu
# Select: 4 (View Recent Logs) 
# Or: 5 (View Container Logs)
```

## 💡 Tips

- **Use Ctrl+C** to exit log viewers (options 4 & 5)
- **Invalid selections** will show error and return to menu
- **Empty inputs** are validated and rejected
- **Menu clears screen** each time for clean interface

---

🎯 **The menu system provides an intuitive interface for all server management tasks!**
