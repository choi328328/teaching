from feedernet import Feedernet
from feedernet_constant import user_config
import os
import json

base_path = '/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/'
executable_path = os.path.join(
    base_path, 'chromedriver_102')

if __name__ == '__main__':
    # chrome drive path
    conncetor = Feedernet(executable_path=executable_path)
    # feedernet 아이디, 비밀번호
    conncetor.login(id=user_config.id, pw=user_config.pw,)

    with open(os.path.join(base_path, 'test.json')) as json_file:
        cohort_definition = json.load(json_file)

    targets = ['AJOUMC',
               'KHNMC',
               'KDH',
               'KWMC',
               'GNUH',
               'KHMC',
               'DCMC',
               'MJH',
               'PNUH',
               'SJMC_BUCHEON',
               'WKUH',
               'EUMC',
               'SJMC_INCHEON',
               'GNUCH']

    targets = ['AJOUMC',
               'KHNMC',
               'KDH',
               'KWMC']

    for num, target in enumerate(targets):
        conncetor.new_tab(f'tab{num}')
        conncetor.search_concept(
            domain='Condition Occurrence', filter='Essential', target=target)
    # for num, target in enumerate(targets):
    #     conncetor.new_tab(f'tab{num}')
    #     conncetor.cohort_generation(cohort_definition=cohort_definition,
    #                                 target=target, cohort_name=None)
