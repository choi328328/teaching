from FRAX import TestFRAX

if __name__ == '__main__':
  
  # Beautifulsoup 
  # Selenium

  url = 'https://www.sheffield.ac.uk/FRAX/tool.aspx?country=25'
  executable_path = './chromedriver_102'
  #os.system(f"spctl --add --label 'Approved' {driver_path}")  #for authorization. Mac only
  calculator=TestFRAX()
  calculator.initialize(executable_path=executable_path, url=url)

  osteo, fracture=calculator.calculate_frax(
          pat_id='Chulhyoung', 
          age=50, 
          year=1974, 
          month=3,
          day=1, 
          female=False, 
          wt=80,
          ht=150,
          previous_fracture=True,
          parent_fractured=True, 
          smoking=True, 
          glucocorticoid=True, 
          rheumatoid=True,
          secondary=False, 
          alcohol=False, 
          femoral_method='T-Score',
          femoral_value=3.0
  )
  
print(osteo, fracture)