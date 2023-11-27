import datetime
from monthdelta import monthdelta

# Today
current_date = datetime.date.today()

# Calculate the date 1year from today
one_year_ago = current_date - datetime.timedelta(days=365)

# Calculate the date 1 month from today
# Use the monthelta library to calculate the month accurately
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