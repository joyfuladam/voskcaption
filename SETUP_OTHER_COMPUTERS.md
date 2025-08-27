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

## ⚙️ **Configuration Setup (Important!)**

After running the setup script, you need to configure the application:

1. **Copy the template configuration:**
   ```bash
   cp config.template.json config.json
   ```

2. **Edit the configuration file:**
   - Open `config.json` in any text editor
   - Add your Azure Speech API key to `"speech_key"`
   - Customize other settings as needed

3. **Get an Azure Speech API key:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a Speech Service resource
   - Copy the key and region

---

## 🐍 **Virtual Environment Workflow**

The setup script creates a **virtual environment** (`venv`) to isolate dependencies:

### **Activating the Virtual Environment:**

#### **macOS & Linux:**
```bash
# Option 1: Manual activation
source venv/bin/activate

# Option 2: Use the activation script
./activate_caption5.sh
```

#### **Windows:**
```bash
# Option 1: Manual activation
venv\Scripts\activate.bat

# Option 2: Use the activation script
activate_caption5.bat
```

### **Running the Application:**
```bash
# Make sure virtual environment is activated (you'll see (venv) in your prompt)
python captionStable.py
```

### **Deactivating:**
```bash
deactivate
```

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

### **Step 3: Create Virtual Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate.bat
```

### **Step 4: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 5: Run the Application**
```bash
python captionStable.py
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

**Note**: The update script automatically handles virtual environment activation when updating dependencies.

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
chmod +x activate_caption5.sh
```

### **Virtual Environment Issues:**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate.bat on Windows
pip install -r requirements.txt
```

### **Dependencies fail to install:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate.bat on Windows
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 📱 **Need Help?**

- Check the main [README.md](README.md) for detailed information
- Look at [WORKFLOW_QUICK_REFERENCE.md](WORKFLOW_QUICK_REFERENCE.md) for daily commands
- The setup scripts will guide you through any issues

---

## 🎉 **You're All Set!**

Once setup is complete, you can:
- ✅ Run Caption5 in an isolated environment
- ✅ Get automatic updates whenever they're available
- ✅ Have the same version as all other computers
- ✅ Contribute back to the project if you want

**Happy Captioning! 🎤**
