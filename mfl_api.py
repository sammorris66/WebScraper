import requests
import smtplib
from email.message import EmailMessage
import os
from tqdm import tqdm

class AcrossThePond:

    def __init__(self, team_name):

        self.league_id = 24073
        self.username = 'morris_data'
        self.password = 'caveman1'
        try:
            assert isinstance(team_name, str)
            self.team_name = team_name
        except Exception:
            raise ValueError('Invalid Team Name, must a String')

    def my_timer(orig_func):
        import time

        def wrapper(*args, **kwargs):
            t1 = time.time()
            result = orig_func(*args, **kwargs)
            t2 = time.time() - t1
            print('{} ran in: {} sec'.format(orig_func.__name__, t2))
            return result

        return wrapper

    @property
    def _cookie(self):
        try:
            r = requests.get('https://api.myfantasyleague.com/2020/standings',
                             params={'USERNAME': self.username, 'PASSWORD': self.password, 'XML': 1})
        except Exception as e:
            print(e)

        cookie = r.cookies.get('MFL_USER_ID')
        return cookie

    @property
    def league_info(self):

        try:
            league_data = requests.get('https://api.myfantasyleague.com/2020/export',
                            params={'TYPE': 'league', 'L' : self.league_id, 'JSON' : 1},
                            headers={'Content-Type': 'application/json'},
                            cookies={'MFL_USER_ID': self._cookie}).json()
        except Exception as e:
            print(e)
        else:
            return league_data

    @property
    def _team_id(self):

        league_data = self.league_info
        fran_id = ''

        for fid in league_data['league']['franchises']['franchise']:
            if fid['name'] == self.team_name:
                fran_id = fid['id']
                return fran_id
        if not fran_id:
            return "Team Name is not in this league"



    def _player_ids(self):

        roster_data = requests.get('https://api.myfantasyleague.com/2020/export',
                                params={'TYPE': 'rosters', 'L' : self.league_id, 'JSON' : 1, 'FRANCHISE': self._team_id},
                                headers={'Content-Type': 'application/json'},
                                cookies={'MFL_USER_ID': self._cookie}).json()
        player_id_list = [pid['id'] for pid in roster_data['rosters']['franchise']['player']]

        return player_id_list

    def player_names(self, player_id_list, fa_only=False):

        name_list_all = []
        assert len(player_id_list) > 0
        for player in player_id_list:
            try:
                player_data = requests.get('https://api.myfantasyleague.com/2020/export',
                                           params={'TYPE': 'playerProfile', 'P': player, 'JSON': 1},
                                           headers={'Content-Type': 'application/json'},
                                           cookies={'MFL_USER_ID': self._cookie}).json()
            except Exception as e:
                print(e)
            else:
                if fa_only is False:
                    name_list_all.append(player_data['playerProfile']['name'])
                else:
                    if 'FA' in player_data['playerProfile']['name']:
                        name_list_all.append(player_data['playerProfile']['name'])
        if name_list_all:
            return name_list_all
        else:
            return 'No free agents on the roster'

    @my_timer
    def get_news(self, latest=False):

        player_list = self._player_ids()
        message_list = []
        # Progress bar context manager
        with tqdm(total=len(player_list)) as pbar:
            pbar.set_description('Player News Progress')
            for player in player_list:
                 pbar.update(1)
                 try:
                     player_data = requests.get('https://api.myfantasyleague.com/2020/export',
                                        params={'TYPE': 'playerProfile', 'P' : player, 'JSON' : 1},
                                        headers={'Content-Type': 'application/json'},
                                        cookies={'MFL_USER_ID': self._cookie}).json()
                 except Exception as e:
                     print(e)
                 else:
                     try:
                         news = player_data['playerProfile']['news']['article']
                         name = player_data['playerProfile']['name']
                     except KeyError:
                         continue
                     else:
                         if isinstance(news, dict):
                             headline = news['headline']
                             news_published = news['published']
                             message_list.append(f'{name} - {news_published} - {headline}')
                         elif isinstance(news, list):
                             if latest:
                                 headline = news[0]['headline']
                                 news_published = news[0]['published']
                                 message_list.append(f'{name} - {news_published} - {headline}')
                             else:
                                 for index, h in enumerate(news, start=1):
                                    headline = h['headline']
                                    news_published = h['published']
                                    message_list.append(f'{index} - {name} - {news_published} - {headline}')
                         else:
                             continue

        message = '\n'.join(message_list)
        return message

    def __repr__(self):
        return str(f'For league id - {self.league_id} & team - {self.team_name}')

    def __len__(self):
        return len(self.player_names())

    def __call__(self):
        print(f'League id - {self.league_id}')
        print(f'Team Name - {self.team_name}')
        print(f'Team Id - {self._team_id}')

    def __eq__(self, other):

        if self.team_name == other.team_name:
            return True
        else:
            return False



    @staticmethod
    def send_email(message, subject='MFL Player News'):

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = 'Sam Morris <samuel.morris1980@gmail.com>'
        msg['To'] = 'sam_morris66@hotmail.com'
        msg.set_content(message)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login('samuel.morris1980@gmail.com', os.environ['email_password'])
            server.send_message(msg)

    def top_adds(self):

        try:
            top_adds_data = requests.get('https://api.myfantasyleague.com/2020/export',
                                  params={'TYPE': 'topAdds', 'Count': 20, 'JSON': 1},
                                  headers={'Content-Type': 'application/json'},
                                  cookies={'MFL_USER_ID': self._cookie}).json()
        except Exception as e:
            print(e)
        else:
            list_players_ids = {adds['id'] for adds in top_adds_data['topAdds']['player']}
            assert len(list_players_ids) > 0
            list_players_percent = {adds['percent'] for adds in top_adds_data['topAdds']['player']}

            names = self.player_names(list_players_ids)

            top_add_dict = {percent: name for percent, name in zip(list_players_percent, names)}

            return top_add_dict


#    def team_history(self):



my_team = AcrossThePond('Morris Dancers')
msg = my_team.get_news(latest=True)
#my_team.send_email(msg)
#print(my_team())
print(my_team.get_news(latest=True))
#print(my_team.get_news(latest=True))

#print(my_team.get_news(latest=True))

#print(my_team.top_adds())




