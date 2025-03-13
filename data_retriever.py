import yfinance as yf
import pandas as pd

def get_stock_data(symbol: str, start, end, interval: str):
    """
    拉取历史数据，返回 DataFrame
    """
    try:
        df = yf.download(symbol, start=start, end=end, interval=interval)
        if not df.empty:
            df.reset_index(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def get_latest_price(symbol: str):
    """
    获取单只股票最新价格，只返回 float 或 str
    """
    try:
        # 注意：不加 group_by='ticker'，让它返回普通一维列
        df = yf.download(symbol, period="1d", interval="1m")
        if not df.empty:
            # df['Close'].iloc[-1] 可能是 float，也可能是 Series
            price_series = df['Close'].iloc[-1]
            
            # 如果是 Series，就取第一个元素
            if isinstance(price_series, pd.Series):
                price_series = price_series.values[0]
            
            price = round(float(price_series), 2)
            return price  # float
    except Exception as e:
        print(f"获取 {symbol} 数据错误：{str(e)}")
    return "N/A"