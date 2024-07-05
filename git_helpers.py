import asyncio
from os import getcwd
from pathlib import Path

from async_lru import alru_cache
from aiofiles.tempfile import TemporaryDirectory

@alru_cache(maxsize=None)
async def check_if_git_exists() -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            'git',
            '--version',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
    except FileNotFoundError:
        raise Exception('git was not found') from None
    stdout, stderr = await proc.communicate()
    try:
        stdout, stderr = stdout.decode('utf-8').replace('\r\n','\n'), stderr.decode('utf-8').replace('\r\n','\n')
    except UnicodeDecodeError:
        stdout, stderr = repr(stdout.replace(b'\r\n',b'\n')), repr(stderr.replace(b'\r\n',b'\n'))
    if stderr or proc.returncode:
        raise Exception(f'git no exist, got error code {proc.returncode} error: {stderr}{stdout}')
    return stdout.strip()


async def run_git_command(cmd: tuple[str], git_repo_dir: str | Path = getcwd()) -> tuple[str,int]:
    proc = await asyncio.create_subprocess_exec(
        'git',
        *cmd,
        cwd=git_repo_dir,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    try:
        stdout, stderr = stdout.decode('utf-8').replace('\r\n','\n'), stderr.decode('utf-8').replace('\r\n','\n')
    except UnicodeDecodeError:
        stdout, stderr = repr(stdout.replace(b'\r\n',b'\n')), repr(stderr.replace(b'\r\n',b'\n'))
    if proc.returncode:
        raise Exception(f'Error when running git command, code {proc.returncode} error: {stderr}{stdout}')
    return stdout.strip() + stderr.strip(),proc.returncode


@alru_cache(maxsize=None)
async def get_git_url() -> tuple[str]:
    branch = (await run_git_command(('remote','show')))[0]
    raw_url,_ =  await run_git_command(('remote','show',branch))
    url = raw_url.split('Fetch URL: ')[1].split('\n')[0].strip()
    return url,branch


@alru_cache(maxsize=None)
async def is_modfied() -> bool:
    out,_ = await run_git_command(('status',))
    
    if 'nothing to commit, working tree clean' in out:
        return False
    return True


@alru_cache(maxsize=None)
async def is_updated() -> bool:
    out,_ = await run_git_command(('fetch','--dry-run'))
    return not out

@alru_cache(maxsize=None)
async def get_commit_count(git_repo_dir: str | Path = getcwd()) -> int:
    count_commit,_ = await run_git_command(('rev-list', '--count', 'HEAD'),git_repo_dir)
    return int(count_commit)
    

async def get_remote_count() -> int:
    remote_url,_ = await get_git_url()
    async with TemporaryDirectory() as tp:
        tp = Path(tp)
        proc = await asyncio.create_subprocess_exec(
            'git',
            'clone',
            remote_url,
            cwd=tp,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        try:
            stdout, stderr = stdout.decode('utf-8').replace('\r\n','\n'), stderr.decode('utf-8').replace('\r\n','\n')
        except UnicodeDecodeError:
            stdout, stderr = repr(stdout.replace(b'\r\n',b'\n')), repr(stderr.replace(b'\r\n',b'\n'))
        if proc.returncode:
            raise Exception(f'Error when running git command, code {proc.returncode} error: {stderr}{stdout}')
        
        for ezwizard_dir in tp.iterdir():
            pass
        
        return await get_commit_count(ezwizard_dir)
        
async def main():
    a = await get_remote_count()
    print(a)
    
if __name__ == '__main__':
    raise SystemExit(asyncio.run(main()))