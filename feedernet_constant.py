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
