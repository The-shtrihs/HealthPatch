from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.core.tasks.auth_tasks import clear_expired_tokens

scheduler = AsyncIOScheduler()

def setup_scheduler():
    scheduler.add_job(
        clear_expired_tokens, 
        trigger='cron', 
        hour=3, 
        minute=0,
        id='clear_tokens_job', 
        replace_existing=True
    )
    
