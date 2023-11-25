import datetime
from monthdelta import monthdelta

# 현재 날짜
current_date = datetime.date.today()

# 1년 전 날짜 계산
one_year_ago = current_date - datetime.timedelta(days=365)

# 1달 전 날짜 계산
# 한 달을 정확히 계산하기 위해 monthdelta 라이브러리 사용
one_month_ago = current_date - monthdelta(1)

def current_time():
    return current_date.strftime('%Y-%m-%d')

def one_year_ago_f():
    return one_year_ago.strftime('%Y-%m-%d')

def one_month_ago_f():
    return one_month_ago.strftime('%Y-%m-%d')

def current_time_t():
    return current_date

def one_year_ago_f_t():
    return one_year_ago

def one_month_ago_f_t():
    return one_month_ago