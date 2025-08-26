# Caption5 Git Workflow - Quick Reference

## 🚀 For Developers (Publishing Updates)

```bash
# 1. Make your changes to the code
# 2. Publish the update
./publish_update.sh

# Or manually:
git add .
git commit -m "Your commit message"
git push origin main
```

## 📥 For Users (Getting Updates)

```bash
# Update to latest version
./update_app.sh

# Or manually:
git pull origin main
```

## 📋 Daily Commands

| Action | Command | When to Use |
|--------|---------|-------------|
| Check status | `git status` | Before making changes |
| See changes | `git diff` | Review what you've modified |
| Stage changes | `git add .` | Before committing |
| Commit changes | `git commit -m "message"` | After staging |
| Push to remote | `git push origin main` | After committing |
| Pull updates | `git pull origin main` | Get latest changes |
| View history | `git log --oneline` | See recent commits |

## 🔧 Common Scenarios

### Making a Quick Fix
```bash
# Edit file, then:
./publish_update.sh
```

### Checking What Changed
```bash
git log --oneline -5  # Last 5 commits
git show HEAD         # Show last commit details
```

### Undoing Changes
```bash
git checkout -- filename  # Undo uncommitted changes
git reset --hard HEAD~1   # Undo last commit (⚠️ destructive)
```

### Branching (Advanced)
```bash
git checkout -b feature-name  # Create new branch
git checkout main             # Switch back to main
git merge feature-name        # Merge feature into main
```

## 🚨 Troubleshooting

- **Push rejected**: Run `git pull origin main` first
- **Merge conflicts**: Edit conflicted files, then `git add .` and `git commit`
- **Authentication errors**: Check your remote URL and credentials

## 📱 Mobile/Quick Updates

For quick updates from mobile or other devices:
```bash
git pull origin main
# Make small changes
git add .
git commit -m "Quick update"
git push origin main
```
