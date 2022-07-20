from dataclasses import dataclass


@dataclass
class user_config:
    id: str = 'choi328328@ajou.ac.kr'
    pw: str = 'qwer1234!@'


@dataclass
class hospital_constant:
    newest_generate = {
        'AJOUMC': 3,
        'KHNMC': 4,
        'KDH': 2,
        'KWMC': 3,
        'GNUH': 3,
        'KHMC': 4,
        'DCMC': 3,
        'MJH': 2,
        'PNUH': 2,
        'SJMC_BUCHEON': 3,
        'WKUH': 4,
        'EUMC': 3,
        'SJMC_INCHEON': 3,
        'GNUCH': 2
    }
    newest_vocabulary = {
        'AJOUMC': 'AUMC_5.3.1_06',
        'KHNMC': 'KHNMC_5.3.1_monthly',
        'KDH': 'KDH_5.3.0_03',
        'KWMC': 'KWMC_5.3.1_monthly',
        'GNUH': 'GNUH_5.3.1_weekly',
        'KHMC': 'KHMC_5.3.1_monthly',
        'DCMC': 'DCMC_5.3.1_weekly',
        'MJH': 'MJH_5.3.0_02',
        'PNUH': 'PNUH_5.3.0_02',
        'SJMC_BUCHEON': 'SEJONG_BCN_5.3.1_daily',
        'WKUH': 'WKUH_5.3.1_weekly',
        'EUMC': 'EUMC_5.3.1_weekly',
        'SJMC_INCHEON': 'SEJONG_ICN_5.3.1_daily',
        'GNUCH': 'GNUCH_5.3.1_01'
    }

    location_urls = {
        'AJOUMC': 'v2.7.6/9/37',
        'KHNMC': 'v2.7.6/7/43',
        'KDH': 'v2.7.6/4/42',
        'KWMC': 'v2.7.6/10/41',
        'GNUH': 'v2.7.6/88/129',
        'KHMC': 'v2.7.6/11/16',
        'DCMC': 'v2.7.6/16/29',
        'MJH': 'v2.7.6/67/101',
        'PNUH': 'v2.7.6/3/36',
        'SJMC_BUCHEON': 'v2.7.6/33/62',
        'WKUH': 'v2.7.6/13/15',
        'EUMC': 'v2.7.6/5/38',
        'SJMC_INCHEON': 'v2.7.6/32/60',
        'GNUCH': 'v2.7.6/86/127',
    }
