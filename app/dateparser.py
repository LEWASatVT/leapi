import datetime
import dateutil.parser
import re

class DateParser: 
    patterns = { r'yesterday': datetime.datetime.now()-datetime.timedelta(days=1),
                 r'([0-9]+) (day|month|year|hour|week)s?': 'ago',
                 r'last (day|second|minute|hour|week)': 'since' }
   
    def __init__(self):
        self.patterns = dict([ (re.compile(k), v) for k,v in DateParser.patterns.items() ])
        pass

    def parse(self, string):
        for regex,f in self.patterns.items():
            m = regex.match(string)
            if m:
                if isinstance(f,str):
                    return getattr(self,f)(*(m.groups()))
                else:
                    return f
        try:
            return dateutil.parser.parse(string)
        except ValueError:
            return None

    def ago(self, count, period):
        args = { period+"s": int(count) }
        return datetime.datetime.now()-datetime.timedelta(**args)

    def since(self, period):
        return self.ago(1, period)

if __name__ == '__main__':
    dp = DateParser()
    
    for exp in ['yesterday', '1 day', '3 days', 'last week']:
        d = dp.parse(exp)
        print(d)

