"""
Git操作技能集
提供常用的Git命令封装
"""

import subprocess


class GitOperations:
    """Git操作工具类"""
    
    @staticmethod
    def run_command(command):
        """执行命令"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Error: {e.stderr}"
    
    @staticmethod
    def status():
        """查看状态"""
        return GitOperations.run_command('git status')
    
    @staticmethod
    def add(files='.'):
        """添加文件"""
        return GitOperations.run_command(f'git add {files}')
    
    @staticmethod
    def commit(message):
        """提交更改"""
        return GitOperations.run_command(f'git commit -m "{message}"')
    
    @staticmethod
    def push(remote='origin', branch='main'):
        """推送到远程"""
        return GitOperations.run_command(f'git push {remote} {branch}')
    
    @staticmethod
    def pull(remote='origin', branch='main'):
        """拉取远程更改"""
        return GitOperations.run_command(f'git pull {remote} {branch}')
    
    @staticmethod
    def branch_list():
        """列出分支"""
        return GitOperations.run_command('git branch')
    
    @staticmethod
    def create_branch(branch_name):
        """创建分支"""
        return GitOperations.run_command(f'git branch {branch_name}')
    
    @staticmethod
    def checkout(branch_name):
        """切换分支"""
        return GitOperations.run_command(f'git checkout {branch_name}')
    
    @staticmethod
    def log(count=10):
        """查看提交历史"""
        return GitOperations.run_command(f'git log --oneline -n {count}')
    
    @staticmethod
    def diff():
        """查看差异"""
        return GitOperations.run_command('git diff')
    
    @staticmethod
    def clone(repo_url, directory=None):
        """克隆仓库"""
        cmd = f'git clone {repo_url}'
        if directory:
            cmd += f' {directory}'
        return GitOperations.run_command(cmd)
