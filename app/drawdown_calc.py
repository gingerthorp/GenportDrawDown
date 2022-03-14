import pandas as _pd
import numpy as _np


class drawdown_calculation:
    def __init__(self, df: _pd.DataFrame):
        self.df = df

    def to_drawdown_series(self, prices):
        """pirce to drawdown"""
        dd = prices / _np.maximum.accumulate(prices) - 1.
        return dd.replace([_np.inf, -_np.inf, -0], 0)

    def drawdown_details(self, drawdown):
        """
        모든 드로다운 기간에 대한 dd 기간의 시작/종료/낙폭일/날짜/기간/최대 DD 정보를 계산.
        """
        # mark no drawdown
        no_dd = drawdown == 0

        # 시작 날짜 추출.
        starts = ~no_dd & no_dd.shift(1)
        starts = list(starts[starts].index)

        # 종료 날짜 추출.
        ends = no_dd & (~no_dd).shift(1)
        ends = list(ends[ends].index)
        # no drawdown :)
        if not starts:
            return _pd.DataFrame(
                index=[], columns=('start', 'valley', 'end', 'days',
                                   'max drawdown'))

        # 처음 부터 우하향 경우 예외 처리.
        # drawdown series begins in a drawdown
        if ends and starts[0] > ends[0]:
            starts.insert(0, drawdown.index[0])

        # DD가 진행 되면서 끝나는 경우 예외 처리.
        # series ends in a drawdown fill with last date
        if not ends or starts[-1] > ends[-1]:
            ends.append(drawdown.index[-1])

        # build dataframe from results
        data = []
        for i, _ in enumerate(starts):
            dd = drawdown[starts[i]:ends[i]]
            data.append((starts[i], dd.idxmin(), ends[i],
                         (ends[i] - starts[i]).days,
                         dd.min() * 100))

        df = _pd.DataFrame(data=data,
                           columns=('start', 'valley', 'end', 'days',
                                    'max drawdown'))
        df['days'] = df['days'].astype(int)
        df['max drawdown'] = df['max drawdown'].astype(float)

        df['start'] = df['start'].dt.strftime('%Y-%m-%d')
        df['end'] = df['end'].dt.strftime('%Y-%m-%d')
        df['valley'] = df['valley'].dt.strftime('%Y-%m-%d')

        return df


if __name__ == '__main__':
    df = _pd.read_csv(f"../csv/dd_table.csv")
    df['nsYMD'] = _pd.to_datetime(df['nsYMD'], format='%Y%m%d')
    df = df.set_index('nsYMD')

    DC = drawdown_calculation(df)

    assets = ["KOSPI", "KOSDAQ", "PORT_ASSET"]

    for asset in assets:
        # price series data
        prices = df[asset]

        # Drawdown 계산.
        dd = DC.to_drawdown_series(prices)

        # Drawdown 상세 결과 테이블 생성.
        dddf = DC.drawdown_details(dd)

        # DD ratio 정렬.
        print(dddf.sort_values(by='max drawdown', ascending=True, kind='mergesort'))

        # DD days 정렬.
        print(dddf.sort_values(by='days', ascending=True, kind='mergesort'))