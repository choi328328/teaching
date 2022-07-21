from FRAX import TestFRAX
import pandas as pd
import time
import os
import numpy as np
if __name__ == '__main__':

    # Beautifulsoup
    # Selenium

    url = 'https://www.sheffield.ac.uk/FRAX/tool.aspx?country=25'
    base_path = '/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/'
    executable_path = os.path.join(base_path, './chromedriver_102')
    # os.system(f"spctl --add --label 'Approved' {driver_path}")  #for authorization. Mac only
    calculator = TestFRAX()
    calculator.initialize(executable_path=executable_path, url=url)

    df = pd.read_excel(
        '/Users/choibyungjin/Library/CloudStorage/OneDrive-아주대학교/study/teaching/FRAX.xlsx')
    df['female'] = np.where(df['sex'] == 'F', True, False)
    np.where(df['sex'] == 'F', True, False)
    for col in ['previous_fracture', 'parent_fractured', 'smoking', 'glucocorticoid',
                'rheumatoid', 'secondary', 'alcohol']:
        np.where(df[col] == 'Y', True, False)
    df.loc[:, ['year', 'month', 'day', 'wt', 'ht',
               'femoral_value']] = df.loc[:, ['year',
                                              'month', 'day', 'wt', 'ht', 'femoral_value']].astype(float)
    df = df.query('''femoral_method == 'Hologic' ''')

    pat_ids, osteos, fractures = [], [], []
    for _, row in df.iterrows():
        osteo, fracture = calculator.calculate_frax(
            pat_id=row['pat_id'],
            age=row['age'],
            year=row['year'],
            month=row['month'],
            day=row['day'],
            female=row['female'],
            wt=row['wt'],
            ht=row['ht'],
            previous_fracture=row['previous_fracture'],
            parent_fractured=row['parent_fractured'],
            smoking=row['smoking'],
            glucocorticoid=row['glucocorticoid'],
            rheumatoid=row['rheumatoid'],
            secondary=row['secondary'],
            alcohol=row['alcohol'],
            femoral_method=row['femoral_method'],
            femoral_value=row['femoral_value']
        )
        pat_ids.append(row['pat_id'])
        osteos.append(osteo)
        fractures.append(fracture)
        time.sleep(3)
    calculated = pd.DataFrame({'pat_id': pat_ids, 'osteo': osteos,
                               'fracture': fractures})
    calculated.to_csv('FRAX_result.csv', index=False)
