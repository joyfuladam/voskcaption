# Setting Up Remote Repository

This guide will help you set up a remote repository so you can publish updates and allow other computers to pull them.

## Option 1: GitHub (Recommended)

### 1. Create a New Repository
1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Name it `caption5` (or your preferred name)
5. Make it **Public** or **Private** (your choice)
6. **Don't** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

### 2. Connect Your Local Repository
After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote origin (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/caption5.git

# Push your existing code to GitHub
git push -u origin main
```

## Option 2: GitLab

### 1. Create a New Project
1. Go to [GitLab.com](https://gitlab.com) and sign in
2. Click "New project"
3. Choose "Create blank project"
4. Name it `caption5`
5. Set visibility level (Public or Private)
6. Click "Create project"

### 2. Connect Your Local Repository
```bash
# Add the remote origin (replace YOUR_USERNAME with your GitLab username)
git remote add origin https://gitlab.com/YOUR_USERNAME/caption5.git

# Push your existing code to GitLab
git push -u origin main
```

## Option 3: Self-Hosted Git Server

If you have your own Git server:

```bash
# Add your custom remote
git remote add origin git@your-server.com:caption5.git

# Push your code
git push -u origin main
```

## Verifying the Setup

After setting up the remote, verify it's working:

```bash
# Check your remotes
git remote -v

# Should show something like:
# origin  https://github.com/YOUR_USERNAME/caption5.git (fetch)
# origin  https://github.com/YOUR_USERNAME/caption5.git (push)
```

## Testing the Workflow

### 1. Make a Test Change
Edit any file (e.g., add a comment to `captionStable.py`)

### 2. Publish the Update
```bash
./publish_update.sh
```

### 3. On Another Computer
```bash
# Clone the repository (first time)
git clone https://github.com/YOUR_USERNAME/caption5.git
cd caption5

# Or update existing copy
./update_app.sh
```

## Troubleshooting

### Authentication Issues
If you get authentication errors:

1. **For HTTPS**: Use a personal access token instead of password
2. **For SSH**: Set up SSH keys with your Git provider

### Push Rejected
If push is rejected:
```bash
# Pull latest changes first
git pull origin main

# Then push again
git push origin main
```

## Next Steps

Once your remote is set up:

1. **For Development**: Use `./publish_update.sh` to commit and push changes
2. **For Users**: Use `./update_app.sh` to pull the latest updates
3. **For Collaboration**: Share the repository URL with your team

## Security Notes

- Keep your repository private if it contains sensitive information
- Use strong authentication (SSH keys or personal access tokens)
- Regularly update your dependencies
- Consider using branch protection rules for production code
