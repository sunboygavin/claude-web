# GitHub 推送说明

## 问题
当前 GitHub token 没有写入权限，无法直接推送代码。

## 解决方案

### 方案 1: 生成新的 Personal Access Token (推荐)

1. 访问: https://github.com/settings/tokens/new
2. 填写:
   - Note: `claude-web-push`
   - Expiration: 选择有效期
   - 勾选权限:
     - ✅ **repo** (完整仓库访问权限)
     - ✅ **workflow** (如果需要 GitHub Actions)
3. 点击 "Generate token"
4. 复制新 token
5. 运行:
```bash
cd /root/claude-web
git remote remove origin
git remote add origin https://新token@github.com/sunboygavin/claude-web.git
git push -u origin main
```

### 方案 2: 使用 SSH (推荐长期使用)

1. 生成 SSH 密钥:
```bash
ssh-keygen -t ed25519 -C "sunboygavin@users.noreply.github.com"
cat ~/.ssh/id_ed25519.pub
```

2. 添加到 GitHub:
   - 访问: https://github.com/settings/keys
   - 点击 "New SSH key"
   - 粘贴公钥内容
   - 点击 "Add SSH key"

3. 配置远程仓库:
```bash
cd /root/claude-web
git remote remove origin
git remote add origin git@github.com:sunboygavin/claude-web.git
git push -u origin main
```

### 方案 3: 手动上传 (临时方案)

1. 打包代码:
```bash
cd /root/claude-web
tar -czf claude-web.tar.gz --exclude=venv --exclude=.git --exclude=*.db --exclude=__pycache__ .
```

2. 下载到本地
3. 在本地解压并推送到 GitHub

## 当前代码状态

✅ 所有代码已提交到本地 git
✅ 共 3 个提交:
- c0ead03 Add upgrade summary for v2.3.0
- a8c8dd8 Add GitHub setup documentation and sync script
- 5910dde Initial commit: Claude Web v2.3.0

✅ 远程仓库已配置: https://github.com/sunboygavin/claude-web

只需要有写入权限的认证方式即可推送。

## 推荐操作

使用方案 1 生成新的 token，确保勾选 **repo** 权限。
