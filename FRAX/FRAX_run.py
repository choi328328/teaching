from FRAX import TestFRAX
import pandas as pd
import time
import os
import numpy as np
import csv
from loguru import logger

if __name__ == "__main__":

    # Beautifulsoup
    # Selenium

    url = "https://www.sheffield.ac.uk/FRAX/tool.aspx?country=25"
    base_path = (
        "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/"
    )
    outpath = "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/FRAX_calculated.csv"
    executable_path = "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/feedernet/chromedriver"
    # os.system(f"spctl --add --label 'Approved' {driver_path}")  #for authorization. Mac only

    df = pd.read_excel(
        "/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/FRAX.xlsx"
    )
    df["female"] = np.where(df["sex"] == "F", True, False)
    np.where(df["sex"] == "F", True, False)
    df.loc[:, ["year", "month", "day", "wt", "ht", "femoral_value"]] = df.loc[
        :, ["year", "month", "day", "wt", "ht", "femoral_value"]
    ].astype(float)
    df = df.dropna(subset=["femoral_value"])
    df = df.query("(age < 90)")

    calculator = TestFRAX()
    calculator.initialize(executable_path=executable_path, url=url)

    pat_ids, osteos, fractures = [], [], []

    with open(outpath, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["pat_id", "osteo", "fracture"])

    for _, row in df.iterrows():
        try:
            pat_id, osteo, fracture = calculator.calculate_frax(
                pat_id=row["pat_id"],
                age=row["age"],
                year=row["year"],
                month=row["month"],
                day=row["day"],
                female=row["female"],
                wt=row["wt"],
                ht=row["ht"],
                previous_fracture=row["previous_fracture"],
                parent_fractured=row["parent_fractured"],
                smoking=row["smoking"],
                glucocorticoid=row["glucocorticoid"],
                rheumatoid=row["rheumatoid"],
                secondary=row["secondary"],
                alcohol=row["alcohol"],
                femoral_method=row["femoral_method"],
                femoral_value=row["femoral_value"],
            )
            pat_ids.append(row["pat_id"])
            osteos.append(osteo)
            fractures.append(fracture)
            time.sleep(3)
            if osteo is not None:
                with open(outpath, "a") as file:
                    spamwriter = csv.writer(file, delimiter=",", lineterminator="\n")
                    spamwriter.writerow([pat_id, osteo, fracture])
        except Exception as e:
            logger.exception(f"Error: {row['pat_id']}")
            time.sleep(3)

    calculated = pd.DataFrame(
        {"pat_id": pat_ids, "osteo": osteos, "fracture": fractures}
    )

    calculated.to_csv("FRAX_result.csv", index=False)
