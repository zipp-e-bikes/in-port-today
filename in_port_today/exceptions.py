class InPortTodayError(Exception):
    pass


class CruiseScheduleError(InPortTodayError):
    pass


class WeatherError(InPortTodayError):
    pass
