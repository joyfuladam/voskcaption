# 🖥️ Setting Up Caption5 on Other Computers

This guide shows you how to set up Caption5 on any new computer in just a few steps!

## 🚀 **Quick Setup (Choose Your Operating System)**

### **macOS & Linux Users:**
```bash
# 1. Open Terminal
# 2. Run this command:
curl -sSL https://raw.githubusercontent.com/joyfuladam/caption/main/setup_new_computer.sh | bash
```

### **Windows Users:**
1. **Download the setup script**: Right-click [this link](https://raw.githubusercontent.com/joyfuladam/caption/main/setup_new_computer.bat) and "Save As"
2. **Run the script**: Double-click `setup_new_computer.bat`

---

## 📋 **Manual Setup (Step by Step)**

### **Step 1: Install Prerequisites**
- **Git**: [Download from git-scm.com](https://git-scm.com/downloads)
- **Python 3.8+**: [Download from python.org](https://python.org/downloads/)

### **Step 2: Clone the Repository**
```bash
git clone https://github.com/joyfuladam/caption.git
cd caption
```

### **Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
# Or on some systems:
pip3 install -r requirements.txt
```

### **Step 4: Run the Application**
```bash
python captionStable.py
# Or on some systems:
python3 captionStable.py
```

---

## 🔄 **Getting Updates**

Once set up, getting updates is super easy:

### **macOS & Linux:**
```bash
./update_app.sh
```

### **Windows:**
```bash
update_app.bat
```

---

## 🌐 **Repository URL**
**https://github.com/joyfuladam/caption.git**

---

## ❓ **Troubleshooting**

### **"Git not found" Error:**
- Install Git from [git-scm.com](https://git-scm.com/downloads)

### **"Python not found" Error:**
- Install Python from [python.org](https://python.org/downloads/)
- Make sure to check "Add Python to PATH" during installation

### **"Permission denied" Error (macOS/Linux):**
```bash
chmod +x setup_new_computer.sh
chmod +x update_app.sh
```

### **Dependencies fail to install:**
```bash
pip install --user -r requirements.txt
```

---

## 📱 **Need Help?**

- Check the main [README.md](README.md) for detailed information
- Look at [WORKFLOW_QUICK_REFERENCE.md](WORKFLOW_QUICK_REFERENCE.md) for daily commands
- The setup scripts will guide you through any issues

---

## 🎉 **You're All Set!**

Once setup is complete, you can:
- ✅ Run Caption5 on the new computer
- ✅ Get automatic updates whenever they're available
- ✅ Have the same version as all other computers
- ✅ Contribute back to the project if you want

**Happy Captioning! 🎤**
