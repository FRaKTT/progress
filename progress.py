import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date, timedelta
from config import PROGRESS_FILE


def get_records_from_file(filename, date_val_splitter='', record_pattern=None):
    """Read file and fill dict [str, int]"""
    if not record_pattern:
        record_pattern = r'\d{4}\.\d{2}\.\d{2}\s*' + date_val_splitter + r'\s*\d+\s*'  # '2020.04.18 431'
    records = {}
    for line in open(filename):
        line = line.strip()
        if re.fullmatch(record_pattern, line):
            record_date, record_value = (field.strip() for field in line.split(date_val_splitter))
            records[record_date] = int(record_value)
    return records


def get_total(filename=PROGRESS_FILE, total_val_splitter=''):
    """Searching record about total value"""
    record_pattern = r'total - \d+'  # 'total - 800'
    total = None
    for line in open(filename):
        line = line.strip()
        if re.fullmatch(record_pattern, line):
            total = int(line.split(total_val_splitter)[1].strip())
            break
    return total


class Progress:
    def __init__(self, filename, val_splitter='', record_pattern=None, date_format_str='%Y.%m.%d'):
        self.records_str = get_records_from_file(filename, val_splitter, record_pattern)
        self.total = get_total(filename, val_splitter)

        # convert date from string to datetime.date format
        self.records_dt = {datetime.strptime(date, date_format_str).date(): value  for date, value in self.records_str.items()}
        # and add current date if it doesn't exist
        today = date.today()
        last_quantity = self.records_dt[max(self.records_dt.keys())]
        self.records_dt[today] = last_quantity

        # convert date to format suitable for plotting
        self.records_mdate = {mdates.date2num(date_dt): value  for date_dt, value in self.records_dt.items()}



    def plot(self):
        """Plot graph of progress"""
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y.%m.%d'))
        # plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.plot(self.records_mdate.keys(), self.records_mdate.values(), marker='o')
        # plt.gcf().autofmt_xdate()

        if self.total: 
            plt.hlines(self.total, min(self.records_mdate.keys()), max(self.records_mdate.keys()), colors='r')

        # ToDo: plot line of progress (average and week)

        plt.xlabel('Date')
        plt.ylabel('Pages')
        plt.grid()
        plt.show()


    def calc_speed(self, start_dt=None, end_dt=None):
        """Returns progress speed in quantities per day"""
        if not start_dt:
            start_dt = min(self.records_dt.keys())
        if not end_dt:
            end_dt = max(self.records_dt.keys())
        delta_quantity = self.records_dt[end_dt] - self.records_dt[start_dt]
        delta_dt = end_dt - start_dt  # datetime.timedelta type
        return delta_quantity / delta_dt.days

    
    def calc_speed_last_n_days(self, last_n_days):
        """Returns progress speed during last N days"""
        today = date.today()
        delta = timedelta(last_n_days)
        start_day = today - delta
        return self.calc_speed(start_dt=start_day)


    def calc_eta(self, last_n_days=None):
        """Estimated time for achievement total value"""
        last_dt = max(self.records_dt.keys())
        quantity_left = self.total - self.records_dt[last_dt]
        if last_n_days:  # uses speed during last N days
            speed = self.calc_speed_last_n_days(last_n_days)
        else:
            speed = self.calc_speed()
        return quantity_left / speed



if __name__ == '__main__':
    progr = Progress(PROGRESS_FILE, '-')
    speed_av = progr.calc_speed()
    # speed_week = progr.calc_speed_last_n_days(7)
    eta_av = progr.calc_eta()
    # eta_week = progr.calc_eta(7)
    print(f'average speed: {speed_av:.2f} pages/day')
    # print(f'week speed: {speed_av:.2f} pages/day')
    print(f'eta (average): {eta_av:.2f} days')
    # print(f'eta (week): {eta_week:.2f} days')
    progr.plot()
