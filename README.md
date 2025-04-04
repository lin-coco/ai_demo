# Ai应用Demo

实现提供Ai翻译、AI总结接口

运行
```bash
# 创建环境
conda create --name ai_demo python=3.9 -y
conda activate ai_demo
pip install -r requirements.txt
# 启动redis
docker run -d -p 6379:6379 --name some-redis redis
# 启动Celery Worker
celery -A tasks.celery worker --loglevel=info
# 启动Flask
python app.py
```

删除
```bash
# 移除redis
docker stop some-redis | docker rm some-redis
# 移除环境
conda remove -n ai_demo --all
```
