import re
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, date, timedelta
from config import PROGRESS_FILE
import argparse


def get_records_from_file(filename, date_val_splitter='', record_pattern=None):
    """Read file and fill 2 lists: dates [str] and quantities [int]"""
    if not record_pattern:
        record_pattern = r'\d{4}\.\d{2}\.\d{2}\s*' + date_val_splitter + r'\s*\d+\s*'  # '2020.04.18 431'
    dates = []
    quantities = []
    for line in open(filename):
        line = line.strip()
        if re.fullmatch(record_pattern, line):
            record_date, record_quantity = (field.strip() for field in line.split(date_val_splitter))
            dates.append(record_date)
            quantities.append(int(record_quantity))
    return dates, quantities


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
        self.dates, self.quantities = get_records_from_file(filename, val_splitter, record_pattern)
        self.total = get_total(filename, val_splitter)

        # convert date from string to datetime.date format
        self.dates_dt = [datetime.strptime(date, date_format_str).date() for date in self.dates]
        # and add current date if it doesn't exist
        today = date.today()
        if self.dates_dt[-1] != today: ####
            last_quantity = self.quantities[-1]
            self.dates_dt.append(today)
            self.quantities.append(last_quantity)

        # convert date to format suitable for plotting
        self.dates_mdate = [mdates.date2num(date_dt) for date_dt in self.dates_dt]


    def plot(self):
        """Plot graph of progress"""
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y.%m.%d'))
        # plt.gca().xaxis.set_major_locator(mdates.DayLocator())
        plt.plot(self.dates_mdate, self.quantities, marker='o')
        # plt.gcf().autofmt_xdate()

        if self.total: 
            plt.hlines(self.total, min(self.dates_mdate), max(self.dates_mdate), colors='r')

        # ToDo: plot line of progress (average and week)

        plt.xlabel('Date')
        plt.ylabel('Pages')
        plt.grid()
        plt.show()


    def quantity_for_date(self, target_date):
        """Find quantity that should correspond for arbitrary date"""
        try:
            i = self.dates_dt.index(target_date)
            return self.quantities[i]
        except ValueError:  # no such date in dates_dt
            quantity = self.quantities[0]  # default start quantity
            for i, date in enumerate(self.dates_dt):
                if date <= target_date:
                    quantity = self.quantities[i]
                else:
                    break
            return quantity


    def calc_speed(self, start_dt=None, end_dt=None):
        """Returns progress speed in quantities per day"""
        if not start_dt:
            start_dt = self.dates_dt[0]
        if not end_dt:
            end_dt = self.dates_dt[-1]
        delta_quantity = self.quantity_for_date(end_dt) - self.quantity_for_date(start_dt)
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
        quantity_left = self.total - self.quantities[-1]
        if last_n_days:  # uses speed during last N days
            speed = self.calc_speed_last_n_days(last_n_days)
        else:
            speed = self.calc_speed()
        return quantity_left / speed



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Analyse and plot the progress.')
    parser.add_argument('--file', nargs='?', default=PROGRESS_FILE, help='File with progress data')
    args = parser.parse_args()
    progress_file = args.file

    progr = Progress(progress_file, '-')
    speed_av = progr.calc_speed()
    speed_week = progr.calc_speed_last_n_days(7)
    eta_av = progr.calc_eta()
    eta_week = progr.calc_eta(7)
    print(f'average speed: {speed_av:.2f} pages/day')
    print(f'week speed: {speed_week:.2f} pages/day')
    print(f'eta (average): {eta_av:.2f} days')
    print(f'eta (week): {eta_week:.2f} days')
    progr.plot()
