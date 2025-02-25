from .tool_defintions import *
from .globals import *

#These are the currently available tools.
toolkits['core'] = [Note_Taker, chat_finalizer]
toolkits['file_management'] = [File_Write, File_Read, File_List]
toolkits['project_management'] = [projects_database, tasks_database, calendar_events, find_people]
toolkits['task_management'] = [tasks_database, calendar_events, find_people]
toolkits['event_management'] = [calendar_events]
toolkits['database_management'] = [Database_Wizard]
toolkits['finance&economics_apipack'] = [currency_exchange_rate, foreign_exchange_time_series, stock_market_time_series, crypto_currency_time_series]