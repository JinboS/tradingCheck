def get_signals(df, short_window=5, long_window=20):
    """
    计算短期均线、长期均线，并生成买卖信号。
    """
    if 'Close' not in df.columns:
        return df
    df['MA_short'] = df['Close'].rolling(window=short_window).mean()
    df['MA_long'] = df['Close'].rolling(window=long_window).mean()
    df['Signal'] = 0
    df.loc[short_window:, 'Signal'] = (
        df['MA_short'][short_window:] > df['MA_long'][short_window:]
    ).astype(int)
    df['Position'] = df['Signal'].diff().fillna(0)
    return df
