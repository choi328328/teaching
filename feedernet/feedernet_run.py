import contextlib
from feedernet import Feedernet
from feedernet_constant import user_config
import os
import json

base_path = (
    "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/feedernet"
)
executable_path = os.path.join(base_path, "chromedriver")


if __name__ == "__main__":
    # chrome drive path
    conncetor = Feedernet(executable_path=executable_path)
    # feedernet 아이디, 비밀번호
    conncetor.login(
        id=user_config.id, pw=user_config.pw,
    )

    targets = [
        "AJOUMC",
        "KHNMC",
        "KDH",
        "KWMC",
        "GNUH",
        "KHMC",
        "DCMC",
        "MJH",
        "PNUH",
        "SJMC_BUCHEON",
        "WKUH",
        "EUMC",
        "SJMC_INCHEON",
        "GNUCH",
    ]

    # for num, target in enumerate(targets):
    #     with contextlib.suppress(Exception):
    #         conncetor.new_tab(f"tab{num}")
    #         conncetor.search_concept(
    #             domain="Measurement", filter="creatinine", target=target
    #         )

    # -----

    json_name, cohort_name = 'pace.json', 'pace'  # test.json
    with open(os.path.join(base_path, json_name)) as json_file:
        cohort_definition = json.load(json_file)

    for num, target in enumerate(targets):
        with contextlib.suppress(Exception):
            conncetor.new_tab(f'tab{num}')
            conncetor.cohort_generation(cohort_definition=cohort_definition,
                                        target=target, cohort_name=cohort_name)

