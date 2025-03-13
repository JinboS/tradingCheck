1. 后端（Flask + yfinance）
获取多只股票数据，并兼容最新 yfinance 行为（MultiIndex 列、NaN/Inf 转换等）
支持自定义时区、数据间隔
计算简单均线交叉买卖信号
返回 JSON 给前端（避免 NaN/Inf JSON 序列化报错）


2. 前端（HTML + JavaScript + Plotly）
模仿 TradingView 风格，左侧仅显示当前选中的股票（K线/蜡烛图）
右侧显示关注列表（Watchlist），列出多只股票及其最新价格，点击后可切换左侧图表
“买卖信号”等指标可用一个复选框来选择是否在图表上显示
支持中文显示
定时自动刷新


运行步骤
安装依赖
pip install flask yfinance pandas pytz numpy


目录结构
your_project/
├─ app.py
└─ templates/
   └─ index.html


启动服务
python app.py
默认监听 http://127.0.0.1:5000/

打开浏览器
访问 http://127.0.0.1:5000/ 即可看到界面。
